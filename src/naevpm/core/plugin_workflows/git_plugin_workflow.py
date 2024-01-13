import os
import shutil

import pygit2

from naevpm.core import git_utils
from naevpm.core.config import Config
from naevpm.core.plugin_workflows.plugin_workflow import PluginWorkflow


class GitPluginWorkflow(PluginWorkflow):

    def fetch_plugin(self, source: str, cache_location: str):
        git_utils.sync_repo(source, cache_location, Config.DEFAULT_GIT_REMOTE_NAME, Config.REGISTRY_GIT_BRANCH_NAME)

    def install_plugin(self, cache_location: str, install_location: str):
        if os.path.exists(install_location):
            shutil.rmtree(install_location)
        shutil.copytree(cache_location, install_location, copy_function=os.link)

    def check_plugin(self, source: str, cache_location: str, install_location: str) -> bool:
        repo = pygit2.Repository(cache_location)
        git_utils.fetch_latest_commit(repo, Config.DEFAULT_GIT_REMOTE_NAME)
        return not git_utils.is_remote_and_local_commit_same(repo, Config.DEFAULT_GIT_REMOTE_NAME,
                                                             Config.DEFAULT_GIT_BRANCH_NAME)

    def update_plugin(self, source: str, cache_location: str, install_location: str):
        # Update cache
        git_utils.sync_repo(source, cache_location, Config.DEFAULT_GIT_REMOTE_NAME, Config.REGISTRY_GIT_BRANCH_NAME)

        # Apply update by deleting installation folder and hard-linking it again to the cache
        if os.path.exists(install_location):
            shutil.rmtree(install_location)
        shutil.copytree(cache_location, install_location, copy_function=os.link)

    def uninstall_plugin(self, install_location: str):
        if os.path.exists(install_location):
            shutil.rmtree(install_location)

    def delete_plugin(self, cache_location: str):
        if os.path.exists(cache_location):
            shutil.rmtree(cache_location)
