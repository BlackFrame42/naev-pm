class PluginWorkflow:
    def fetch_plugin(self, source: str, cache_location: str):
        pass

    def install_plugin(self, cache_location: str, install_location: str):
        pass

    def check_plugin(self, source: str, cache_location: str, install_location: str) -> bool:
        pass

    def update_plugin(self, source: str, cache_location: str, install_location: str):
        pass

    def uninstall_plugin(self, install_location: str):
        pass

    def delete_plugin(self, cache_location: str):
        pass
