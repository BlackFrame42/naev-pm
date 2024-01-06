import base64
import os
import shutil
from datetime import datetime, timezone
from hashlib import md5
from typing import Optional
import pygit2
from lxml import etree
from urllib.parse import quote

from naevpm.core import git_utils
from naevpm.core.abstract_thread_communication import AbstractCommunication
from naevpm.core.config import Config
from naevpm.core.directories import Directories
from naevpm.core.git_utils import OriginNotFound
from naevpm.core.models import PluginDbModel, RegistryDbModel, RegistryPluginMetaDataModel, PluginState, \
    PluginMetaDataModel
from naevpm.core.sqlite_database_connector import SqliteDatabaseConnector, RegistrySourceUniqueConstraintViolation


class ApplicationLogicRegistrySourceWasAlreadyAdded(Exception):
    pass


class ApplicationLogicEmptyRegistrySource(Exception):
    pass


class ApplicationLogic:
    database_connector: SqliteDatabaseConnector

    def __init__(self, database_connector: SqliteDatabaseConnector):
        super().__init__()
        self.database_connector = database_connector

    def _get_folder_name_for_registry(self, source: str) -> str:
        # Still add some part of the source to the name, so that it can be recognized in the file browser by a human
        basename = os.path.basename(os.path.normpath(source))
        # source cannot be directly used as a unique folder name. Create a hash encoded in base64 instead.
        return base64.urlsafe_b64encode(md5(source.encode('utf-8')).digest()).decode('utf-8') + '_' + basename

    def _get_folder_name_for_plugin_name_and_source(self, name: str, source: str):
        encoded_name = quote(name)
        return base64.urlsafe_b64encode(md5(source.encode('utf-8')).digest()).decode(
            'utf-8') + '_' + encoded_name

    def _get_folder_name_for_plugin(self, plugin: PluginDbModel) -> str:
        return self._get_folder_name_for_plugin_name_and_source(plugin.name, plugin.source)

    def _get_absolute_registry_folder_path(self, registry_folder_name: str) -> str:
        return os.path.join(Directories.REGISTRIES, registry_folder_name)

    def _get_absolute_registry_folder_path2(self, registry: RegistryDbModel):
        registry_folder_name = self._get_folder_name_for_registry(registry.source)
        return self._get_absolute_registry_folder_path(registry_folder_name)

    def _get_absolute_cached_plugin_folder_path(self, plugin_folder_name: str) -> str:
        return os.path.join(Directories.PLUGINS_CACHE, plugin_folder_name)

    def _get_absolute_cached_plugin_folder_path2(self, plugin: PluginDbModel) -> str:
        plugin_folder_name = self._get_folder_name_for_plugin(plugin)
        return os.path.join(Directories.PLUGINS_CACHE, plugin_folder_name)

    def _get_absolute_cached_plugin_xml_path(self, plugin: PluginDbModel) -> str:
        absolute_cached_plugin_folder_path = self._get_absolute_cached_plugin_folder_path2(plugin)
        return os.path.join(absolute_cached_plugin_folder_path, 'plugin.xml')

    def _get_absolute_plugin_installation_folder_path(self, plugin_folder_name: str) -> str:
        return os.path.join(Directories.NAEV_PLUGIN_DIR, plugin_folder_name)

    def _all_plugin_metadata_file_paths(self, folder: str) -> list[str]:
        xml_files = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith('.xml'):
                    xml_files.append(os.path.join(root, file))
        return xml_files

    def _parse_registry_plugin_metadata_xml_file(self, file_path: str) -> RegistryPluginMetaDataModel:
        """
        Specification at https://github.com/naev/naev-plugins#plugin-information-format
        """
        with open(file_path, 'r') as f:
            text_content = f.read()
            plugin = etree.XML(text_content.encode('utf-8'))
            return RegistryPluginMetaDataModel(
                name=plugin.get("name"),
                # TODO currently, git is used as source. ZIP links should also be possible in the future
                source=plugin.findtext("git"),
                author=plugin.findtext("author"),
                license=plugin.findtext("license"),
                website=plugin.findtext("website")
            )

    def _parse_plugin_metadata_xml_file(self, xml_path: str) -> PluginMetaDataModel:
        """
              Specification at https://github.com/naev/naev/blob/main/docs/manual/sec/plugins.md#plugin-meta-data-pluginxml
              """
        with open(xml_path, 'r') as f:
            text_content = f.read()
            plugin = etree.XML(text_content.encode('utf-8'))
            priority = plugin.findtext("priority")
            priority_int = None
            if priority is not None:
                priority_int = int(priority)
            return PluginMetaDataModel(
                name=plugin.get("name"),
                author=plugin.findtext("author"),
                version=plugin.findtext("version"),
                description=plugin.findtext("description"),
                compatibility=plugin.findtext("compatibility"),
                priority=priority_int,
                source=plugin.findtext("source"),
                blacklist=plugin.xpath(f'./blacklist/text()'),
                total_conversion=len(plugin.xpath(f'./total_conversion')) > 0,
                whitelist=plugin.xpath(f'./whitelist/text()')
            )

    def parse_plugin_metadata_xml_file(self, plugin: PluginDbModel) -> PluginMetaDataModel:
        file_path = self._get_absolute_cached_plugin_xml_path(plugin)
        return self._parse_plugin_metadata_xml_file(file_path)

    def _read_cached_registry(self, absolute_registry_folder_path: str) -> list[RegistryPluginMetaDataModel]:
        """
        @param absolute_registry_folder_path:
        @return: All plugin metadata found in plugins folder of registry.
        """
        plugin_metadatas = []
        plugin_xml_dir = os.path.join(absolute_registry_folder_path, Config.PLUGIN_XML_DIR)
        for absolute_xml_file_path in self._all_plugin_metadata_file_paths(plugin_xml_dir):
            plugin_metadata = self._parse_registry_plugin_metadata_xml_file(absolute_xml_file_path)
            plugin_metadatas.append(plugin_metadata)
        return plugin_metadatas

    def add_registry(self, source: str, tc: AbstractCommunication) -> RegistryDbModel:
        """
        @raise  ApplicationLogicEmptyRegistrySource
        @raise  RegistrySourceUniqueConstraintViolation
        """
        tc.message(f"Adding: Registry {source}")
        if source.strip() == '':
            raise ApplicationLogicEmptyRegistrySource()
        registry = RegistryDbModel(source)
        try:
            self.database_connector.add_registry(registry)
        except RegistrySourceUniqueConstraintViolation:
            raise ApplicationLogicRegistrySourceWasAlreadyAdded()
        tc.message(f"Added: Registry {source}")
        return registry

    # ----------------------------------NEW
    def _sync_repo(self, source: str, target: str, tc: AbstractCommunication):
        tc.message(f"Syncing: {source} -> {target}")
        git_utils.sync_repo(source, target, Config.DEFAULT_GIT_REMOTE_NAME, Config.REGISTRY_GIT_BRANCH_NAME)
        tc.message(f"Synced: {source} -> {target}")

    def _hard_link(self, source: str, target: str, tc: AbstractCommunication):
        tc.message(f"Hard-linking: {source} -> {target}")
        # Delete target first if it already exists
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(source, target, copy_function=os.link)
        tc.message(f"Hard-linked: {source} -> {target}")

    def _read_plugin_metadatas(self,
                               absolute_registry_folder_path: str,
                               tc: AbstractCommunication) -> list[RegistryPluginMetaDataModel]:
        tc.message(f"Reading: {absolute_registry_folder_path}")
        plugin_metadatas = self._read_cached_registry(absolute_registry_folder_path)
        tc.message(f"Read: {absolute_registry_folder_path}")
        return plugin_metadatas

    def _save_plugin_metadatas(self, source: str,
                               plugin_metadatas: list[RegistryPluginMetaDataModel],
                               tc: AbstractCommunication):
        tc.message(f"Saving: Plugin metadata from {source}")
        for plugin_metadata in plugin_metadatas:
            self.database_connector.index_plugin(source, plugin_metadata)
        tc.message(f"Saved: Plugin metadata from {source}")

    def _save_registry_last_fetched(self, registry: RegistryDbModel, tc: AbstractCommunication):
        # Make sure to create a timezone-aware datetime object
        tc.message(f"Saving: Registry field last_fetched for registry {registry.source}")
        last_fetched = datetime.now(timezone.utc)
        self.database_connector.set_registry_last_fetched(registry.source, last_fetched)
        registry.last_fetched = datetime.now(tz=timezone.utc)
        tc.message(f"Saved: Registry field last_fetched '{str(last_fetched)}' for registry {registry.source}")

    def _delete_folder_recursively(self, path: str, tc: AbstractCommunication):
        tc.message(f"Deleting: Path {path}")
        if os.path.exists(path):
            shutil.rmtree(path)
        tc.message(f"Deleted: Path {path}")

    def _save_plugin_state(self, plugin: PluginDbModel, state: PluginState, tc: AbstractCommunication):
        tc.message(f"Saving: State '{state.name}' for plugin {plugin.source}")
        self.database_connector.set_plugin_state(plugin.source, state)
        plugin.state = state
        tc.message(f"Saved: State '{state.name}' for plugin {plugin.source}")

    def _fetch_latest_commit(self, repo: pygit2.Repository, tc: AbstractCommunication):
        tc.message(f"Fetching: Latest commit for repo {repo.path}")
        git_utils.fetch_latest_commit(
            repo,
            Config.DEFAULT_GIT_REMOTE_NAME)
        tc.message(f"Fetched: Latest commit for repo {repo.path}")

    def _save_plugin_update_available(self, plugin: PluginDbModel, update_available: bool, tc: AbstractCommunication):
        tc.message(f"Saving: Plugin field update_available '{str(update_available)}' for plugin {plugin.source}")
        self.database_connector.set_plugin_update_available(plugin.source, update_available)
        plugin.update_available = update_available
        tc.message(f"Saved: Plugin field update_available '{str(update_available)}' for plugin {plugin.source}")

    def _is_remote_and_local_commit_same(self, repo: pygit2.Repository):
        return git_utils.is_remote_and_local_commit_same(repo, Config.DEFAULT_GIT_REMOTE_NAME,
                                                         Config.DEFAULT_GIT_BRANCH_NAME)

    def fetch_registry_plugin_metadatas(self, registry: RegistryDbModel, tc: AbstractCommunication):
        tc.message(f"Fetching: Plugin meta from {registry.source}")
        if registry.source == Directories.LOCAL_REGISTRY:
            # Skip fetch from git remote as there is none for local registry
            plugin_metadatas = self._read_plugin_metadatas(Directories.LOCAL_REGISTRY, tc)
        else:
            absolute_registry_folder_path = self._get_absolute_registry_folder_path2(registry)
            # Make sure the registry repo is uptodate
            self._sync_repo(registry.source, absolute_registry_folder_path, tc)
            # Read XML files in the registry repo to get plugin metadata
            plugin_metadatas = self._read_plugin_metadatas(absolute_registry_folder_path, tc)
        # Save in DB
        self._save_plugin_metadatas(registry.source, plugin_metadatas, tc)
        # set last_fetched field
        self._save_registry_last_fetched(registry, tc)
        tc.message(f"Fetched: Plugin meta data from {registry.source}")

    def remove_plugin_from_index(self, plugin: PluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.INDEXED
        tc.message(f"Removing: Plugin {plugin.source} from index")
        self.database_connector.remove_plugin(plugin.source)
        tc.message(f"Removed: Plugin {plugin.source} from index")

    def fetch_plugin(self, plugin: PluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.INDEXED
        tc.message(f"Fetching: Plugin from {plugin.source}")
        absolute_cached_plugin_folder_path = self._get_absolute_cached_plugin_folder_path2(plugin)
        self._sync_repo(plugin.source, absolute_cached_plugin_folder_path, tc)
        self._save_plugin_state(plugin, PluginState.CACHED, tc)
        tc.message(f"Fetched: Plugin from {plugin.source}")

    def delete_plugin_from_cache(self, plugin: PluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.CACHED
        tc.message(f"Deleting: Plugin {plugin.source} from cache")
        absolute_cached_plugin_folder_path = self._get_absolute_cached_plugin_folder_path2(plugin)
        self._delete_folder_recursively(absolute_cached_plugin_folder_path, tc)
        self._save_plugin_state(plugin, PluginState.INDEXED, tc)
        tc.message(f"Deleted: Plugin {plugin.source} from cache")

    def install_plugin_from_cache(self, plugin: PluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.CACHED
        tc.message(f"Installing: Plugin {plugin.source} from cache")
        plugin_folder_name = self._get_folder_name_for_plugin(plugin)
        absolute_cached_plugin_folder_path = self._get_absolute_cached_plugin_folder_path(plugin_folder_name)
        absolute_plugin_installation_folder_path = (
            self._get_absolute_plugin_installation_folder_path(plugin_folder_name))
        # Create hard links for the whole tree. Using hard links instead of a symbolic links
        # has the advantage of not producing broken links if the linked files are deleted, e.g. when the cache is
        # cleared.
        self._hard_link(absolute_cached_plugin_folder_path, absolute_plugin_installation_folder_path, tc)
        self._save_plugin_state(plugin, PluginState.INSTALLED, tc)
        tc.message(f"Installed: Plugin {plugin.source} from cache at {absolute_plugin_installation_folder_path}")

    def uninstall_plugin(self, plugin: PluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.INSTALLED
        tc.message(f"Uninstalling: Plugin {plugin.source}")
        plugin_folder_name = self._get_folder_name_for_plugin(plugin)
        absolute_plugin_installation_folder_path = (
            self._get_absolute_plugin_installation_folder_path(plugin_folder_name))
        self._delete_folder_recursively(absolute_plugin_installation_folder_path, tc)
        self._save_plugin_state(plugin, PluginState.CACHED, tc)
        tc.message(f"Uninstalled: Plugin {plugin.source} from {absolute_plugin_installation_folder_path}")

    def check_for_plugin_update(self, plugin: PluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.INSTALLED
        tc.message(f"Checking for updates: Plugin {plugin.source}")
        plugin_folder_name = self._get_folder_name_for_plugin(plugin)
        absolute_cached_plugin_folder_path = self._get_absolute_cached_plugin_folder_path(plugin_folder_name)
        cached_plugin_repo = pygit2.Repository(absolute_cached_plugin_folder_path)
        try:
            self._fetch_latest_commit(cached_plugin_repo, tc)
            # Check if fetched remote branch has another (newer) commit:
            if not self._is_remote_and_local_commit_same(cached_plugin_repo):
                self._save_plugin_update_available(plugin, True, tc)
            tc.message(f"Checked for updates: Plugin {plugin.source}")
        except OriginNotFound:
            tc.message(f"Check for updates failed. Plugin {plugin.source} does not have any remote repo.")

    def update_plugin(self, plugin: PluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.INSTALLED
        tc.message(f"Updating: Plugin {plugin.source}")
        plugin_folder_name = self._get_folder_name_for_plugin(plugin)
        absolute_cached_plugin_folder_path = self._get_absolute_cached_plugin_folder_path(plugin_folder_name)
        # Update cache
        self._sync_repo(plugin.source, absolute_cached_plugin_folder_path, tc)
        # Apply update by deleting installation folder and hard-linking it again to the cache
        absolute_plugin_installation_folder_path = (
            self._get_absolute_plugin_installation_folder_path(plugin_folder_name))
        self._delete_folder_recursively(absolute_plugin_installation_folder_path, tc)
        self._hard_link(
            absolute_cached_plugin_folder_path,
            absolute_plugin_installation_folder_path,
            tc
        )
        # Clear update available flag after updating
        self._save_plugin_update_available(plugin, False, tc)
        tc.message(f"Updated: Plugin {plugin.source}")

    def remove_registry(self, registry: RegistryDbModel, tc: AbstractCommunication):
        tc.message(f"Removing: Registry {registry.source}")
        self.database_connector.remove_registry(registry.source)
        tc.message(f"Removed: Registry {registry.source}")

    def get_registries(self) -> list[RegistryDbModel]:
        return self.database_connector.get_registries()

    def get_registry(self, source: str) -> Optional[RegistryDbModel]:
        return self.database_connector.get_registry(source)

    def get_plugins(self) -> list[PluginDbModel]:
        return self.database_connector.get_plugins()

    def get_plugin(self, source: str) -> Optional[PluginDbModel]:
        return self.database_connector.get_plugin(source)

    def _convert_plugin_metadata_to_registry_plugin_metadata(self,
                                                             plugin_metadata: PluginMetaDataModel) -> RegistryPluginMetaDataModel:
        return RegistryPluginMetaDataModel(
            name=plugin_metadata.name,
            source=plugin_metadata.source,
            author=plugin_metadata.author,
            # TODO read LICENSE file of plugin installation
            license=None,
            # TODO currently website is not in plugin metadata specification
            website=None
        )

    def _convert_registry_plugin_metadata_to_xml(self, registry_plugin_metadata: RegistryPluginMetaDataModel) -> bytes:
        xml_plugin = etree.Element('plugin', name=registry_plugin_metadata.name)
        xml_author = etree.Element('author')
        xml_author.text = registry_plugin_metadata.author
        xml_plugin.append(xml_author)
        # TODO make sure correct field is used -> currently only git for repos supported. Upcoming: ZIP link
        xml_git = etree.Element('git')
        xml_plugin.append(xml_git)
        xml_git.text = registry_plugin_metadata.source
        xml_license = etree.Element('license')
        xml_plugin.append(etree.Element('license'))
        xml_license.text = registry_plugin_metadata.license
        xml_website = etree.Element('website')
        xml_plugin.append(xml_website)
        xml_website.text = registry_plugin_metadata.website
        return etree.tostring(xml_plugin, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def import_existing_plugins_to_index(self, tc: AbstractCommunication):
        # Create a new local registry if one does not exist yet
        if not os.path.exists(Directories.LOCAL_REGISTRY):
            absolute_local_registry_plugins_folder = os.path.join(Directories.LOCAL_REGISTRY, 'plugins')
            os.makedirs(absolute_local_registry_plugins_folder)

            pygit2.init_repository(Directories.LOCAL_REGISTRY, False)

        for entry in os.listdir(Directories.NAEV_PLUGIN_DIR):
            absolute_installed_plugin_path = os.path.join(Directories.NAEV_PLUGIN_DIR, entry)
            if os.path.isdir(absolute_installed_plugin_path):
                absolute_plugin_metadata_xml_path = (
                    os.path.join(Directories.NAEV_PLUGIN_DIR, entry, 'plugin.xml'))
                if os.path.exists(absolute_plugin_metadata_xml_path):
                    plugin_metadata = (
                        self._parse_plugin_metadata_xml_file(absolute_plugin_metadata_xml_path))
                    source = plugin_metadata.source
                    if source is not None:
                        # Check if plugin is already indexed ( in db )
                        db_plugin = self.database_connector.get_plugin(source)
                        if db_plugin is None:
                            plugin_folder_name = self._get_folder_name_for_plugin_name_and_source(
                                plugin_metadata.name,
                                plugin_metadata.source
                            )
                            absolute_cached_plugin_folder = self._get_absolute_cached_plugin_folder_path(
                                plugin_folder_name
                            )
                            self._hard_link(absolute_installed_plugin_path, absolute_cached_plugin_folder, tc)

                            # Rename installed plugin folder so it is identical to cached folder
                            new_absolute_installed_plugin_path = os.path.join(Directories.NAEV_PLUGIN_DIR,
                                                                              plugin_folder_name)
                            os.rename(absolute_installed_plugin_path, new_absolute_installed_plugin_path)

                            # create XML representation of plugin metadata in the registry
                            registry_plugin_metadata = self._convert_plugin_metadata_to_registry_plugin_metadata(
                                plugin_metadata)
                            xml = self._convert_registry_plugin_metadata_to_xml(registry_plugin_metadata)
                            absolute_registry_plugins_folder_path = os.path.join(Directories.LOCAL_REGISTRY, 'plugins')
                            registry_plugin_xml_file_name = plugin_folder_name + '.xml'
                            absolute_registry_plugin_xml_path = os.path.join(absolute_registry_plugins_folder_path,
                                                                             registry_plugin_xml_file_name)
                            # Make sure folders exist
                            if not os.path.exists(absolute_registry_plugins_folder_path):
                                os.makedirs(absolute_registry_plugins_folder_path)
                            with open(absolute_registry_plugin_xml_path, 'bw') as f:
                                f.write(xml)

                            # Make sure local registry exists in database
                            # TODO maybe move outside loop
                            if not self.database_connector.exists_registry(Directories.LOCAL_REGISTRY):
                                self.database_connector.add_registry(RegistryDbModel(
                                    source=Directories.LOCAL_REGISTRY,
                                    last_fetched=datetime.now(timezone.utc)
                                ))
                            # Add plugin to index
                            self.database_connector.index_plugin(Directories.LOCAL_REGISTRY, registry_plugin_metadata)
                            self.database_connector.set_plugin_state(source, PluginState.INSTALLED)

                            # Update local registry git repo
                            local_registry_repo = pygit2.Repository(Directories.LOCAL_REGISTRY)
                            index = local_registry_repo.index
                            repo_relative_plugin_xml_path = os.path.join('plugins', registry_plugin_xml_file_name)
                            index.add(repo_relative_plugin_xml_path)
                            index.write()
                            ref = "HEAD"
                            author = pygit2.Signature('naev-pm', 'dummy@mail.address')
                            committer = pygit2.Signature('naev-pm', 'dummy@mail.address')
                            message = "Add " + repo_relative_plugin_xml_path
                            tree = index.write_tree()
                            parents = []
                            local_registry_repo.create_commit(ref, author, committer, message, tree, parents)
                        else:
                            # Check installed plugin's state
                            if db_plugin.state == PluginState.INDEXED:
                                # Copy to cache and set state to INSTALLED
                                absolute_cached_plugin_folder = self._get_absolute_cached_plugin_folder_path2(db_plugin)
                                absolute_installed_plugin_path = os.path.join(Directories.NAEV_PLUGIN_DIR, entry)
                                self._hard_link(absolute_installed_plugin_path, absolute_cached_plugin_folder, tc)
                                self.database_connector.set_plugin_state(db_plugin.source, PluginState.INSTALLED)
                            elif db_plugin.state == PluginState.CACHED:
                                # Assume that cache is in sync with installed plugin
                                self.database_connector.set_plugin_state(db_plugin.source, PluginState.INSTALLED)
                                pass
                            elif db_plugin.state == PluginState.INSTALLED:
                                # Already imported
                                pass
                            else:
                                raise NotImplementedError()
