import logging
from tkinter import StringVar, messagebox
from typing import Optional, Any

from naevpm.core.application_logic import ApplicationLogic, ApplicationLogicRegistrySourceWasAlreadyAdded, \
    ApplicationLogicEmptyRegistrySource
from naevpm.core.models import PluginDbModel, RegistryDbModel, PluginState, PluginMetaDataModel

from naevpm.core.sqlite_database_connector import SqliteDatabaseConnector
from naevpm.gui.abstract_gui_controller import AbstractGuiController

from naevpm.gui.plugins_frame import PluginsFrame
from naevpm.gui.registries_frame import RegistriesFrame
from naevpm.gui.tk_root import TkRoot
from naevpm.gui.tk_threading import TkThreading, ThreadCommunication

logger = logging.getLogger(__name__)


# noinspection PyUnusedLocal
class GuiController(AbstractGuiController):
    registries_frame: RegistriesFrame = None
    plugins_frame: PluginsFrame = None
    status_text: StringVar = None
    root: TkRoot
    tk_threading: TkThreading

    application_logic: ApplicationLogic

    database_connector: SqliteDatabaseConnector

    def __init__(self, database_connector: SqliteDatabaseConnector, root: TkRoot, tk_threading: TkThreading,
                 application_logic: ApplicationLogic):
        super().__init__()
        self.application_logic = application_logic
        self.tk_threading = tk_threading
        self.root = root
        self.database_connector = database_connector

    def add_registry(self, source: str):
        def task(tc: ThreadCommunication) -> RegistryDbModel:
            return self.application_logic.add_registry(source, tc)

        def callback(registry: RegistryDbModel, e: Optional[Exception] = None):
            if e is None:
                self.registries_frame.add_registry_window.withdraw()
                self.registries_frame.put_registry(registry)
            else:
                if isinstance(e, ApplicationLogicRegistrySourceWasAlreadyAdded):
                    messagebox.showerror(parent=self.registries_frame.add_registry_window,
                                         title="Registry source already exists",
                                         message=f"The chosen registry source '{source}' was already added.")
                elif isinstance(e, ApplicationLogicEmptyRegistrySource):
                    messagebox.showerror(parent=self.registries_frame.add_registry_window,
                                         title="Registry source empty",
                                         message=f"The field 'source' must not be empty")
                else:
                    # Reraise in GUI thread if not handled
                    self.show_status(f'Unhandled error occurred: {str(e)}')
                    raise e

        self.tk_threading.run_threaded_task('remove_registry', task, callback)

    def refresh_registries_list(self):
        def task(tc: ThreadCommunication) -> list[RegistryDbModel]:
            return self.database_connector.get_registries()

        def callback(registries: list[RegistryDbModel], e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.registries_frame.put_registries(registries)

        self.tk_threading.run_threaded_task('refresh_registries_list', task, callback)

    def remove_registry(self, registry: RegistryDbModel):
        def task(tc: ThreadCommunication):
            self.application_logic.remove_registry(registry, tc)

        def callback(return_value: Any, e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.registries_frame.remove_registry(registry)

        self.tk_threading.run_threaded_task('remove_registry', task, callback)

    def fetch_registry_plugin_metadatas(self, registry: RegistryDbModel):
        def task(tc: ThreadCommunication):
            self.application_logic.fetch_registry_plugin_metadatas(registry, tc)

        def callback(return_value: Any, e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.registries_frame.update_registry(registry)
            self.refresh_plugins_list()

        self.tk_threading.run_threaded_task('fetch_registry_plugin_metadatas', task, callback)

    def refresh_plugins_list(self):
        def task(tc: ThreadCommunication) -> list[PluginDbModel]:
            return self.database_connector.get_plugins()

        def callback(plugins: list[PluginDbModel], e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.plugins_frame.put_plugins(plugins)

        self.tk_threading.run_threaded_task('refresh_plugins_list', task, callback)

    def install_plugin_from_cache(self, plugin: PluginDbModel):
        def task(tc: ThreadCommunication):
            self.application_logic.install_plugin_from_cache(plugin, tc)

        def callback(return_value: Any, e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                raise e
            self.plugins_frame.update_plugin(plugin)

        self.tk_threading.run_threaded_task('install_plugin_from_cache', task, callback)

    def uninstall_plugin(self, plugin: PluginDbModel):
        def task(tc: ThreadCommunication):
            self.application_logic.uninstall_plugin(plugin, tc)

        def callback(return_value: Any, e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.plugins_frame.update_plugin(plugin)

        self.tk_threading.run_threaded_task('uninstall_plugin', task, callback)

    def delete_plugin_from_cache(self, plugin: PluginDbModel):
        def task(tc: ThreadCommunication):
            self.application_logic.delete_plugin_from_cache(plugin, tc)

        def callback(return_value: Any, e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.plugins_frame.update_plugin(plugin)

        self.tk_threading.run_threaded_task('delete_plugin_from_cache', task, callback)

    def check_for_plugin_update(self, plugin: PluginDbModel):
        def task(tc: ThreadCommunication):
            self.application_logic.check_for_plugin_update(plugin, tc)

        def callback(return_value: Any, e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.plugins_frame.update_plugin(plugin)

        self.tk_threading.run_threaded_task('check_for_plugin_update', task, callback)

    def update_plugin(self, plugin: PluginDbModel):
        def task(tc: ThreadCommunication):
            self.application_logic.update_plugin(plugin, tc)

        def callback(return_value: Any, e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.plugins_frame.update_plugin(plugin)

        self.tk_threading.run_threaded_task('update_plugin', task, callback)

    def check_for_plugin_updates(self, plugins: list[PluginDbModel]):
        for plugin in plugins:
            if plugin.state == PluginState.INSTALLED:
                self.check_for_plugin_update(plugin)

    def fetch_plugin(self, plugin: PluginDbModel):
        def task(tc: ThreadCommunication):
            self.application_logic.fetch_plugin(plugin, tc)

        def callback(return_value: Any, e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.plugins_frame.update_plugin(plugin)
            self.show_plugin_details(plugin)

        self.tk_threading.run_threaded_task('fetch_plugin', task, callback)

    def remove_plugin_from_index(self, plugin: PluginDbModel):
        def task(tc: ThreadCommunication):
            self.application_logic.remove_plugin_from_index(plugin, tc)

        def callback(return_value: Any, e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.plugins_frame.remove_plugin(plugin)

        self.tk_threading.run_threaded_task('remove_plugin_from_index', task, callback)

    def show_status(self, value: str):
        self.status_text.set(value)

    def show_plugin_details(self, plugin: PluginDbModel):
        def task(tc: ThreadCommunication):
            plugin_meta_data = self.application_logic.parse_plugin_metadata_xml_file(plugin)
            return plugin_meta_data

        def callback(plugin_meta_data: PluginMetaDataModel, e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.plugins_frame.show_plugin_details(plugin, plugin_meta_data)

        self.tk_threading.run_threaded_task('remove_plugin_from_index', task, callback)

    def import_existing_plugins_to_index(self):
        def task(tc: ThreadCommunication):
            self.application_logic.import_existing_plugins_to_index(tc)

        def callback(return_value, e: Optional[Exception] = None):
            # Reraise in GUI thread if not handled
            if e is not None:
                self.show_status(f'Unhandled error occurred: {str(e)}')
                raise e
            self.refresh_plugins_list()
            self.refresh_registries_list()

        self.tk_threading.run_threaded_task('remove_plugin_from_index', task, callback)

