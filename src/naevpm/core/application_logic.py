import base64
import os
import shutil
import zipfile
from datetime import datetime, timezone
from hashlib import md5
from typing import Optional
from lxml import etree

from naevpm.core import git_utils
from naevpm.core.abstract_thread_communication import AbstractCommunication
from naevpm.core.config import Config
from naevpm.core.models import IndexedPluginDbModel, RegistryDbModel, RegistryPluginMetaDataModel, \
    PluginMetadataDbModel
from naevpm.core.plugin_workflows.plugin_workflow_manager import PluginWorkflowManager
from naevpm.core.sqlite_database_connector import SqliteDatabaseConnector, RegistrySourceUniqueConstraintViolation


class ApplicationLogicRegistrySourceWasAlreadyAdded(Exception):
    pass


class ApplicationLogicEmptyRegistrySource(Exception):
    pass


class ApplicationLogic:
    database_connector: SqliteDatabaseConnector
    plugin_workflow_manager: PluginWorkflowManager
    config: Config

    def __init__(self, database_connector: SqliteDatabaseConnector, config: Config):
        super().__init__()
        self.config = config
        self.database_connector = database_connector
        self.plugin_workflow_manager = PluginWorkflowManager(database_connector, config)

    def _get_folder_name_for_registry(self, source: str) -> str:
        # Still add some part of the source to the name, so that it can be recognized in the file browser by a human
        basename = os.path.basename(os.path.normpath(source))
        # source cannot be directly used as a unique folder name. Create a hash encoded in base64 instead.
        return base64.urlsafe_b64encode(md5(source.encode('utf-8')).digest()).decode('utf-8') + '_' + basename

    def _get_absolute_registry_folder_path(self, registry_folder_name: str) -> str:
        return os.path.join(self.config.REGISTRIES, registry_folder_name)

    def _get_absolute_registry_folder_path2(self, registry: RegistryDbModel):
        registry_folder_name = self._get_folder_name_for_registry(registry.source)
        return self._get_absolute_registry_folder_path(registry_folder_name)

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

    def _parse_plugin_metadata_xml_string(self, xml_string: str):
        plugin = etree.XML(xml_string.encode('utf-8'))
        priority = plugin.findtext("priority")
        priority_int = None
        if priority is not None:
            priority_int = int(priority)
        return PluginMetadataDbModel(
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

    def _parse_plugin_metadata_xml_file(self, xml_path: str) -> PluginMetadataDbModel:
        """
        Specification at https://github.com/naev/naev/blob/main/docs/manual/sec/plugins.md#plugin-meta-data-pluginxml
        """
        with open(xml_path, 'r') as f:
            text_content = f.read()
            return self._parse_plugin_metadata_xml_string(text_content)

    def parse_plugin_metadata_xml_file(self, plugin: IndexedPluginDbModel) -> Optional[PluginMetadataDbModel]:
        cache_location, install_location = self.plugin_workflow_manager.get_locations(plugin)
        if plugin.source.endswith('.zip'):
            with zipfile.ZipFile(cache_location) as z:
                fd = None
                try:
                    fd = z.open('plugin.xml', 'r')
                    return self._parse_plugin_metadata_xml_string(fd.read().decode('utf-8'))
                except KeyError:
                    return None
                finally:
                    if fd is not None:
                        fd.close()
        else:
            file_path = os.path.join(cache_location, 'plugin.xml')
            return self._parse_plugin_metadata_xml_file(file_path)

    def _read_cached_registry(self, absolute_registry_folder_path: str) -> list[RegistryPluginMetaDataModel]:
        """
        @param absolute_registry_folder_path:
        @return: All plugin metadata found in plugins folder of registry.
        """
        plugin_metadatas = []
        plugin_xml_dir = os.path.join(absolute_registry_folder_path, self.config.PLUGIN_XML_DIR)
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
        git_utils.sync_repo(source, target, self.config.DEFAULT_GIT_REMOTE_NAME, self.config.REGISTRY_GIT_BRANCH_NAME)
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

    def fetch_registry_plugin_metadatas(self, registry: RegistryDbModel, tc: AbstractCommunication):
        tc.message(f"Fetching: Plugin meta from {registry.source}")
        if registry.source == self.config.LOCAL_REGISTRY:
            # Skip fetch from git remote as there is none for local registry
            plugin_metadatas = self._read_plugin_metadatas(self.config.LOCAL_REGISTRY, tc)
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

    def remove_registry(self, registry: RegistryDbModel, tc: AbstractCommunication):
        tc.message(f"Removing: Registry {registry.source}")
        self.database_connector.remove_registry(registry.source)
        tc.message(f"Removed: Registry {registry.source}")

    def get_registries(self) -> list[RegistryDbModel]:
        return self.database_connector.get_registries()

    def get_registry(self, source: str) -> Optional[RegistryDbModel]:
        return self.database_connector.get_registry(source)

    def get_plugins(self) -> list[IndexedPluginDbModel]:
        return self.database_connector.get_plugins()

    def get_plugin(self, source: str) -> Optional[IndexedPluginDbModel]:
        return self.database_connector.get_plugin(source)

    def _convert_plugin_metadata_to_registry_plugin_metadata(self, plugin_metadata: PluginMetadataDbModel) \
            -> RegistryPluginMetaDataModel:
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

    def install_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        self.plugin_workflow_manager.install_plugin(plugin, tc)

    def uninstall_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        self.plugin_workflow_manager.uninstall_plugin(plugin, tc)

    def delete_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        self.plugin_workflow_manager.delete_plugin(plugin, tc)

    def check_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        self.plugin_workflow_manager.check_plugin(plugin, tc)

    def update_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        self.plugin_workflow_manager.update_plugin(plugin, tc)

    def fetch_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        self.plugin_workflow_manager.fetch_plugin(plugin, tc)

    def remove_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        self.plugin_workflow_manager.remove_plugin(plugin, tc)

    def get_plugin_metadata(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication) -> PluginMetadataDbModel:
        tc.message(f"Getting: Plugin metadata {plugin.source}")

        # Try the source in the registry plugin metadata first
        # TODO A bit messy here. Maybe check somewhere if source in registry is same as in plugin.xml
        db_plugin_metadata = self.database_connector.get_plugin_metadata(plugin.source)
        if db_plugin_metadata is None:
            plugin_metadata = self.parse_plugin_metadata_xml_file(plugin)
            # Check if the source in the plugin metadata from the xml is already used
            db_plugin_metadata2 = self.database_connector.get_plugin_metadata(plugin.source)
            if db_plugin_metadata2 is None:
                self.database_connector.insert_plugin_metadata(plugin_metadata)
                return plugin_metadata
            else:
                return db_plugin_metadata2
        tc.message(f"Got: Plugin metadata {plugin.source}")
        return db_plugin_metadata
