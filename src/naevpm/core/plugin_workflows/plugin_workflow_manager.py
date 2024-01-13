import base64
import os
import re
from hashlib import md5
from urllib.parse import urlparse

from naevpm.core.abstract_thread_communication import AbstractCommunication
from naevpm.core.config import Config
from naevpm.core.models import IndexedPluginDbModel, PluginState
from naevpm.core.plugin_workflows.git_plugin_workflow import GitPluginWorkflow
from naevpm.core.plugin_workflows.local_zip_plugin_workflow import LocalZipPluginWorkflow
from naevpm.core.plugin_workflows.plugin_workflow import PluginWorkflow
from naevpm.core.plugin_workflows.remote_zip_plugin_workflow import RemoteZipPluginWorkflow
from naevpm.core.sqlite_database_connector import SqliteDatabaseConnector

unsafe_chars_pattern = re.compile(r'[^0-9a-zA-Z_]')


class PluginWorkflowManager:
    database_connector: SqliteDatabaseConnector
    local_zip_plugin_workflow: PluginWorkflow
    remote_zip_plugin_workflow: PluginWorkflow
    git_plugin_workflow: PluginWorkflow
    config: Config

    def __init__(self, database_connector: SqliteDatabaseConnector, config: Config):
        super().__init__()
        self.config = config
        self.database_connector = database_connector
        self.local_zip_plugin_workflow = LocalZipPluginWorkflow()
        self.remote_zip_plugin_workflow = RemoteZipPluginWorkflow()
        self.git_plugin_workflow = GitPluginWorkflow()

    def _get_workflow(self, plugin: IndexedPluginDbModel) -> PluginWorkflow:
        is_remote = False
        is_zip = False
        if urlparse(plugin.source).scheme != '':
            # Source is most likely a URL
            is_remote = True
        if plugin.source.endswith('.zip'):
            is_zip = True
        if is_remote and is_zip:
            return self.remote_zip_plugin_workflow
        elif not is_remote and is_zip:
            return self.local_zip_plugin_workflow
        else:
            return self.git_plugin_workflow

    def _get_source_hash(self, source: str):
        return base64.urlsafe_b64encode(md5(source.encode('utf-8')).digest()).decode(
            'utf-8')

    def get_locations(self, plugin: IndexedPluginDbModel) -> tuple[str, str]:
        # Modify plugin name so it is safe for filesystem use
        safe_name = unsafe_chars_pattern.sub('_', plugin.name)
        file_system_name = self._get_source_hash(plugin.source) + '_' + safe_name
        suffix = ''
        if plugin.source.endswith('.zip'):
            suffix = '.zip'
        cache_location = str(os.path.join(self.config.PLUGINS_CACHE, file_system_name + suffix))
        install_location = str(os.path.join(self.config.NAEV_PLUGIN_DIR, file_system_name + suffix))
        return cache_location, install_location

    def _save_plugin_state(self, plugin: IndexedPluginDbModel, state: PluginState, tc: AbstractCommunication):
        tc.message(f"Saving: State '{state.name}' for plugin {plugin.source}")
        self.database_connector.set_plugin_state(plugin.source, state)
        plugin.state = state
        tc.message(f"Saved: State '{state.name}' for plugin {plugin.source}")

    def _save_plugin_update_available(self, plugin: IndexedPluginDbModel, update_available: bool,
                                      tc: AbstractCommunication):
        tc.message(f"Saving: Plugin field update_available '{str(update_available)}' for plugin {plugin.source}")
        self.database_connector.set_plugin_update_available(plugin.source, update_available)
        plugin.update_available = update_available
        tc.message(f"Saved: Plugin field update_available '{str(update_available)}' for plugin {plugin.source}")

    def remove_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.INDEXED
        tc.message(f"Removing: Plugin {plugin.source} from index")
        self.database_connector.remove_plugin(plugin.source)
        tc.message(f"Removed: Plugin {plugin.source} from index")

    def fetch_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.INDEXED
        tc.message(f"Fetching: Plugin from {plugin.source}")
        cache_location, install_location = self.get_locations(plugin)
        self._get_workflow(plugin).fetch_plugin(plugin.source, cache_location)
        self._save_plugin_state(plugin, PluginState.CACHED, tc)
        tc.message(f"Fetched: Plugin from {plugin.source}")

    def install_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.CACHED
        tc.message(f"Installing: Plugin {plugin.source} from cache")
        cache_location, install_location = self.get_locations(plugin)
        self._get_workflow(plugin).install_plugin(cache_location, install_location)
        self._save_plugin_state(plugin, PluginState.INSTALLED, tc)
        tc.message(f"Installed: Plugin {plugin.source} from cache at {cache_location}")

    def check_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.INSTALLED
        tc.message(f"Checking for updates: Plugin {plugin.source}")
        cache_location, install_location = self.get_locations(plugin)
        update_available = self._get_workflow(plugin).check_plugin(plugin.source, cache_location, install_location)
        if update_available:
            self._save_plugin_update_available(plugin, True, tc)
        else:
            self._save_plugin_update_available(plugin, False, tc)
        tc.message(f"Checked for updates: Plugin {plugin.source}")

    def update_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.INSTALLED
        tc.message(f"Updating: Plugin {plugin.source}")
        cache_location, install_location = self.get_locations(plugin)
        self._get_workflow(plugin).update_plugin(plugin.source, cache_location, install_location)
        # Clear update available flag after updating
        self._save_plugin_update_available(plugin, False, tc)
        tc.message(f"Updated: Plugin {plugin.source}")

    def uninstall_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.INSTALLED
        tc.message(f"Uninstalling: Plugin {plugin.source}")
        cache_location, install_location = self.get_locations(plugin)
        self._get_workflow(plugin).uninstall_plugin(install_location)
        self._save_plugin_state(plugin, PluginState.CACHED, tc)
        tc.message(f"Uninstalled: Plugin {plugin.source} from {install_location}")

    def delete_plugin(self, plugin: IndexedPluginDbModel, tc: AbstractCommunication):
        assert plugin.state == PluginState.CACHED
        tc.message(f"Deleting: Plugin {plugin.source} from cache")
        cache_location, install_location = self.get_locations(plugin)
        self._get_workflow(plugin).delete_plugin(cache_location)
        self._save_plugin_state(plugin, PluginState.INDEXED, tc)
        tc.message(f"Deleted: Plugin {plugin.source} from cache")
