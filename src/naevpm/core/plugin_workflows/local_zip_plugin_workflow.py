import os

from naevpm.core.plugin_workflows.plugin_workflow import PluginWorkflow


class LocalZipPluginWorkflow(PluginWorkflow):

    def fetch_plugin(self, source: str, cache_location: str):
        if os.path.exists(cache_location):
            os.remove(cache_location)
        os.link(source, cache_location)

    def install_plugin(self, cache_location: str, install_location: str):
        if os.path.exists(install_location):
            os.remove(install_location)
        os.link(cache_location, install_location)

    def check_plugin(self, source: str, cache_location: str, install_location: str) -> bool:
        # if same file (hard-linking), no need to update
        if os.path.exists(source) and os.path.exists(cache_location):
            if os.path.samefile(source, cache_location):
                if os.path.exists(install_location) and os.path.samefile(cache_location, install_location):
                    return False
        return True

    def update_plugin(self, source: str, cache_location: str, install_location: str):
        # Possibly no need to update because of hard-linking

        if os.path.exists(source):
            if os.path.exists(cache_location):
                if os.path.samefile(source, cache_location):
                    if os.path.exists(install_location):
                        if os.path.samefile(cache_location, install_location):
                            return
                        else:
                            os.remove(install_location)
                else:
                    os.remove(cache_location)
                    os.link(source, cache_location)
                    if os.path.exists(install_location):
                        os.remove(install_location)
            else:
                os.link(source, cache_location)
                if os.path.exists(install_location):
                    os.remove(install_location)
            os.link(cache_location, install_location)
        else:
            raise RuntimeError('ZIP plugin source does not exist for update!')

    def uninstall_plugin(self, install_location: str):
        if os.path.exists(install_location):
            os.remove(install_location)

    def delete_plugin(self, cache_location: str):
        if os.path.exists(cache_location):
            os.remove(cache_location)








