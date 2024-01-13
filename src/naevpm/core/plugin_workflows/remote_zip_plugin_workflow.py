import os
from hashlib import md5

import requests

from naevpm.core.plugin_workflows.local_zip_plugin_workflow import LocalZipPluginWorkflow


class RemoteZipPluginWorkflow(LocalZipPluginWorkflow):

    def _fetch_plugin(self, source: str, cache_location: str):
        response = requests.get(source, stream=True)
        response.raise_for_status()
        # Make sure it is a new inode by deleting an existing file first
        if os.path.exists(cache_location):
            os.remove(cache_location)
        with open(cache_location, 'wb') as fd:
            for chunk in response.iter_content(chunk_size=1024*16):
                fd.write(chunk)

    def fetch_plugin(self, source: str, cache_location: str):
        self._fetch_plugin(source, cache_location)

    def check_plugin(self, source: str, cache_location: str, install_location: str) -> bool:
        if not os.path.exists(install_location):
            return True
        self._fetch_plugin(source, cache_location)
        with open(cache_location, 'rb') as f:
            cached_hash = md5(f.read()).hexdigest()
        with open(install_location, 'rb') as f:
            installed_hash = md5(f.read()).hexdigest()
        return cached_hash != installed_hash

    def update_plugin(self, source: str, cache_location: str, install_location: str):
        install_exists = os.path.exists(install_location)
        if os.path.exists(cache_location):
            if install_exists and os.path.samefile(cache_location, install_location):
                return
        else:
            self._fetch_plugin(source, cache_location)
        if install_exists:
            os.remove(install_location)
        os.link(cache_location, install_location)

