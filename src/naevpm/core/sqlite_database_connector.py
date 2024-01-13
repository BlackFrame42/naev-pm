import json
import logging
import sqlite3
from datetime import datetime, timezone
from sqlite3 import Connection, IntegrityError, Cursor
from typing import Optional

from naevpm.core.models import IndexedPluginDbModel, RegistryDbModel, RegistryPluginMetaDataModel, registry_fields, \
    indexed_plugin_fields, \
    PluginState, PluginMetadataDbModel, plugin_metadata_fields

logger = logging.getLogger(__name__)
if sqlite3.threadsafety != 3:
    logger.critical("The underlying SQLite library your python version is using is not in the 'Serialized' mode which "
                    "this application requires for multi-threaded database access. Sources: "
                    "https://www.sqlite.org/threadsafe.html, https://sqlite.org/compile.html#threadsafe and "
                    "https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety")


# According to python documentation, if threadsafety level is 3:
# "Serialized: In serialized mode, SQLite can be safely used by multiple threads with no restriction.
# So, I am going to believe that and deactivate the multi-thread error in python with check_same_thread=False

class RegistrySourceUniqueConstraintViolation(Exception):
    pass


def dict_factory(cursor: Cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def indexed_plugin_factory(cursor: Cursor, row):
    obj = dict_factory(cursor, row)
    state = obj['state']
    if state is not None:
        obj['state'] = PluginState[obj['state']]

    return IndexedPluginDbModel(**obj)


def plugin_metadata_factory(cursor: Cursor, row):
    obj = dict_factory(cursor, row)
    if obj['blacklist'] is not None:
        obj['blacklist'] = json.loads(obj['blacklist'])
    if obj['whitelist'] is not None:
        obj['whitelist'] = json.loads(obj['whitelist'])
    return PluginMetadataDbModel(**obj)


def registry_factory(cursor: Cursor, row):
    obj = dict_factory(cursor, row)
    # Make sure datetime strings are converted into objects
    last_fetched = obj['last_fetched']
    if last_fetched is not None:
        obj['last_fetched'] = datetime.fromisoformat(obj['last_fetched'])
    return RegistryDbModel(**obj)


class SqliteDatabaseConnector:
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS registry (
        source                 text primary key,
        last_fetched           text
    );
    CREATE TABLE IF NOT EXISTS indexed_plugin (
        name                 text,
        author               text,
        license              text,
        website              text,
        source               text primary key,
        installed            bool,
        cached              bool,
        update_available    bool,
        registry_source              text ,
        state               text,
        source_type         text,
        FOREIGN KEY(registry_source) REFERENCES registry(source) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS plugin_metadata (
            name text,
            author text,
            version text,
            description text,
            compatibility text,
            priority integer,
            source text primary key,
            blacklist JSON,
            total_conversion bool,
            whitelist JSON
    )
    """
    db: Connection

    def __init__(self, path: str):
        super().__init__()

        # db file will be created if it does not exist already
        # See header of this file for check_same_thread reasoning. Allows multi-threaded access.
        self.db = sqlite3.connect(path, check_same_thread=False)

        # Make sure tables exist
        self.db.executescript(self.SCHEMA)

        # Enable foreign key constraints
        self.db.execute('PRAGMA foreign_keys = ON;')
        self.db.commit()

    def add_registry(self, registry: RegistryDbModel) -> None:
        try:
            self.db.execute("""INSERT INTO registry (source, last_fetched) VALUES (?,?)""", [
                registry.source,
                registry.last_fetched
            ])
            self.db.commit()
        except IntegrityError as e:
            if len(e.args) > 0:
                if e.args[0] == 'UNIQUE constraint failed: registry.source':
                    raise RegistrySourceUniqueConstraintViolation()
            raise e

    def remove_registry(self, source: str) -> None:
        self.db.execute("DELETE FROM registry WHERE source = ?;", [source])
        self.db.commit()

    def get_registries(self) -> list[RegistryDbModel]:
        cur = self.db.cursor()
        cur.row_factory = registry_factory
        return cur.execute(f"SELECT {','.join(registry_fields)} FROM registry ORDER BY source;").fetchall()

    def get_registry(self, source: str) -> Optional[RegistryDbModel]:
        cur = self.db.cursor()
        cur.row_factory = registry_factory
        return cur.execute(
            f"SELECT {','.join(registry_fields)} FROM registry WHERE source = ?", [source]
        ).fetchone()

    def set_registry_last_fetched(self, source: str, last_fetched: datetime):
        self.db.execute("""UPDATE registry SET last_fetched = ? WHERE source = ?""", [
            last_fetched.astimezone(tz=timezone.utc).isoformat(),
            source
        ])
        self.db.commit()

    def index_plugin(self, registry_source: str, registry_plugin_meta_data: RegistryPluginMetaDataModel):
        """
        Used to UPDATE indexed_plugin list from registry index. Overwrites only fields provided by the index.
        """
        db_plugin = self.db.execute(
            """SELECT * FROM indexed_plugin WHERE source = ?""",
            [registry_plugin_meta_data.source]).fetchone()
        if db_plugin is None:
            self.db.execute("""
                INSERT INTO indexed_plugin (name, author, license, website,
                                    source, registry_source, state)
                VALUES             (?,?,?,?,?,?,?);
                """,
                            [
                                registry_plugin_meta_data.name,
                                registry_plugin_meta_data.author,
                                registry_plugin_meta_data.license,
                                registry_plugin_meta_data.website,
                                registry_plugin_meta_data.source,
                                registry_source,
                                PluginState.INDEXED.name
                            ]
                            )
        else:
            self.db.execute("""
                UPDATE indexed_plugin SET author=?, license=?, website=?,
                                    name=?, registry_source=? WHERE source=?;
                """,
                            [
                                registry_plugin_meta_data.author,
                                registry_plugin_meta_data.license,
                                registry_plugin_meta_data.website,
                                registry_plugin_meta_data.name,
                                registry_source,

                                registry_plugin_meta_data.source
                            ]
                            )
        self.db.commit()

    def get_plugins(self) -> list[IndexedPluginDbModel]:
        cur = self.db.cursor()
        cur.row_factory = indexed_plugin_factory
        return cur.execute(f"SELECT {','.join(indexed_plugin_fields)} FROM indexed_plugin ORDER BY name, source;").fetchall()

    def get_plugin(self, source: str) -> Optional[IndexedPluginDbModel]:
        cur = self.db.cursor()
        cur.row_factory = indexed_plugin_factory
        return cur.execute(
            f"SELECT {','.join(indexed_plugin_fields)} FROM indexed_plugin WHERE source = ?", [source]
        ).fetchone()

    def exists_plugin(self, source: str) -> bool:
        return self.db.execute('SELECT EXISTS(SELECT 1 FROM indexed_plugin WHERE source=? LIMIT 1);',
                               [source]).fetchone()[0]

    def exists_registry(self, source: str) -> bool:
        return self.db.execute('SELECT EXISTS(SELECT 1 FROM registry WHERE source=? LIMIT 1);',
                               [source]).fetchone()[0]

    def remove_plugin(self, source: str) -> None:
        self.db.execute("DELETE FROM indexed_plugin WHERE source = ?", [source])
        self.db.commit()

    def set_plugin_state(self, source: str, state: PluginState):
        self.db.execute("""UPDATE indexed_plugin SET state = ? WHERE source = ?""", [
            state.name,
            source
        ])
        self.db.commit()

    def set_plugin_update_available(self, source: str, update_available: bool):
        self.db.execute("""UPDATE indexed_plugin SET update_available = ? WHERE source = ?""", [
            update_available,
            source
        ])
        self.db.commit()

    def get_plugin_metadata(self, source: str) -> Optional[PluginMetadataDbModel]:
        cur = self.db.cursor()
        cur.row_factory = plugin_metadata_factory
        return cur.execute(
            f"SELECT {','.join(plugin_metadata_fields)} FROM plugin_metadata WHERE source = ?", [source]
        ).fetchone()

    def insert_plugin_metadata(self, plugin_meta_data: PluginMetadataDbModel):
        self.db.execute("""
            INSERT INTO plugin_metadata (name, author, version, description, compatibility, 
                    priority, source, blacklist, total_conversion, whitelist)
            VALUES             (?,?,?,?,?,?,?,?,?,?);
            """,
                        [
                            plugin_meta_data.name,
                            plugin_meta_data.author,
                            plugin_meta_data.version,
                            plugin_meta_data.description,
                            plugin_meta_data.compatibility,
                            plugin_meta_data.priority,
                            plugin_meta_data.source,
                            json.dumps(plugin_meta_data.blacklist),
                            plugin_meta_data.total_conversion,
                            json.dumps(plugin_meta_data.whitelist)
                        ]
                        )
