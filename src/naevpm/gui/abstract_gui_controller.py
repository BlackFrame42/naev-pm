from naevpm.core.models import IndexedPluginDbModel, RegistryDbModel


class AbstractGuiController:

    def refresh_registries_list(self):
        pass

    def add_registry(self, source: str):
        pass

    def remove_registry(self, registry: RegistryDbModel):
        pass

    def fetch_registry_plugin_metadatas(self, registry: RegistryDbModel):
        pass

    def refresh_plugins_list(self):
        pass

    def install_plugin(self, plugin: IndexedPluginDbModel):
        pass

    def uninstall_plugin(self, plugin: IndexedPluginDbModel):
        pass

    def delete_plugin(self, plugin: IndexedPluginDbModel):
        pass

    def check_plugin(self, plugin: IndexedPluginDbModel):
        pass

    def update_plugin(self, plugin: IndexedPluginDbModel):
        pass

    def check_for_plugin_updates(self, plugins: list[IndexedPluginDbModel]):
        pass

    def show_status(self, value: str):
        pass

    def remove_plugin(self, plugin: IndexedPluginDbModel):
        pass

    def fetch_plugin(self, plugin: IndexedPluginDbModel):
        pass

    def show_plugin_details(self, plugin: IndexedPluginDbModel):
        pass

    def import_existing_plugins_to_index(self):
        pass
