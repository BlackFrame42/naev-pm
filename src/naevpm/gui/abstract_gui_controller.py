from naevpm.core.models import PluginDbModel, RegistryDbModel


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

    def install_plugin_from_cache(self, plugin: PluginDbModel):
        pass

    def uninstall_plugin(self, plugin: PluginDbModel):
        pass

    def delete_plugin_from_cache(self, plugin: PluginDbModel):
        pass

    def check_for_plugin_update(self, plugin: PluginDbModel):
        pass

    def update_plugin(self, plugin: PluginDbModel):
        pass

    def check_for_plugin_updates(self, plugins: list[PluginDbModel]):
        pass

    def show_status(self, value: str):
        pass

    def remove_plugin_from_index(self, plugin: PluginDbModel):
        pass

    def fetch_plugin(self, plugin: PluginDbModel):
        pass

    def show_plugin_details(self, plugin: PluginDbModel):
        pass

    def import_existing_plugins_to_index(self):
        pass
