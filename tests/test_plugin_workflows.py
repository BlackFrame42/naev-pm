import os
import shutil
import unittest
import uuid

import pygit2

from naevpm.core.abstract_thread_communication import AbstractCommunication
from naevpm.core.config import Config
from naevpm.core.models import IndexedPluginDbModel, PluginState
from naevpm.core.plugin_workflows.plugin_workflow_manager import PluginWorkflowManager
from naevpm.core.sqlite_database_connector import SqliteDatabaseConnector
from unittest.mock import patch, MagicMock


class TestConfig(Config):
    def __init__(self, ):
        super().__init__("temp/naev-package-manager", "temp/naev")

        if not os.path.exists(self.NAEV_PLUGIN_DIR):
            os.makedirs(self.NAEV_PLUGIN_DIR)


class TestPluginWorkflows(unittest.TestCase):

    @patch('naevpm.core.plugin_workflows.remote_zip_plugin_workflow.requests')
    def test_remote_zip(self, mock):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b'cool works']
        mock.get.return_value = mock_response

        if os.path.exists('temp/naev-package-manager'):
            shutil.rmtree('temp/naev-package-manager')
        if os.path.exists('temp/naev'):
            shutil.rmtree('temp/naev')

        config = TestConfig()

        database_connector = SqliteDatabaseConnector(config.DATABASE)
        plugin_workflow_manager = PluginWorkflowManager(database_connector, config)
        plugin = IndexedPluginDbModel(
            name='test',
            source='http://nonexistent.domain/test.zip',
            state=PluginState.INDEXED
        )
        tc = AbstractCommunication()
        plugin_workflow_manager.fetch_plugin(plugin, tc)
        self.assertTrue(os.path.exists('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))
        self.assertEqual(plugin.state, PluginState.CACHED)
        # Fetching if it already exists but database is not in sync should not be a problem
        plugin.state = PluginState.INDEXED
        plugin_workflow_manager.fetch_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.CACHED)
        self.assertTrue(os.path.exists('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))

        plugin_workflow_manager.install_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.INSTALLED)
        self.assertTrue(os.path.exists('temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))
        # Accept installation even if database is out of sync (plugin is installed but not marked as such)
        plugin.state = PluginState.CACHED
        plugin_workflow_manager.install_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.INSTALLED)
        self.assertTrue(os.path.exists('temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))

        plugin_workflow_manager.check_plugin(plugin, tc)
        self.assertFalse(plugin.update_available)
        # Change source
        mock_response.iter_content = lambda chunk_size: [b'changed response']
        plugin_workflow_manager.check_plugin(plugin, tc)
        self.assertTrue(plugin.update_available)
        # After update, cache and installation should be same
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip',
                                         'temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))
        self.assertFalse(plugin.update_available)
        plugin_workflow_manager.check_plugin(plugin, tc)
        self.assertFalse(plugin.update_available)

        # Delete plugin before update check. non-existent plugin installation is treated as a plugin that can be
        # updated
        os.remove('temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip')
        plugin_workflow_manager.check_plugin(plugin, tc)
        self.assertTrue(plugin.update_available)
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip',
                                         'temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))
        self.assertFalse(plugin.update_available)

        # Try update again (although source is linked with cache and installation)
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip',
                                         'temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))
        self.assertFalse(plugin.update_available)

        # Meddle with installation then overwrite
        with open('temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip', 'w') as f:
            f.write(str(uuid.uuid4()))
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip',
                                         'temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))
        self.assertFalse(plugin.update_available)

        # Replace installation, then overwrite with update
        os.remove('temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip')
        with open('temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip', 'w') as f:
            f.write(str(uuid.uuid4()))
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip',
                                         'temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))
        self.assertFalse(plugin.update_available)

        # Meddle with cache
        os.remove('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip')
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip',
                                         'temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))
        self.assertFalse(plugin.update_available)

        # Make sure download errors are propagated correctly
        # noinspection PyUnusedLocal
        def fn(chunk_size):
            raise RuntimeError()

        mock_response.iter_content = fn
        os.remove('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip')
        try:
            plugin_workflow_manager.update_plugin(plugin, tc)
            self.assertFalse(True, 'never reach')
        except RuntimeError:
            pass

        plugin_workflow_manager.uninstall_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.CACHED)
        self.assertFalse(os.path.exists('temp/naev/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))

        # Accept inconsistency in db (already uninstalled but marked as installed):
        plugin.state = PluginState.INSTALLED
        plugin_workflow_manager.uninstall_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.CACHED)

        plugin_workflow_manager.delete_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.INDEXED)
        self.assertFalse(os.path.exists('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))

        # Accept inconsistency in db (already deleted from cache but marked as cached):
        plugin.state = PluginState.CACHED
        plugin_workflow_manager.delete_plugin(plugin, tc)
        self.assertFalse(os.path.exists('temp/naev-package-manager/plugins/cWTVqe1rMEqIEYtnaH74DA==_test.zip'))

        plugin_workflow_manager.remove_plugin(plugin, tc)
        self.assertIsNone(database_connector.get_plugin('http://nonexistent.domain/test.zip'))

    def test_local_zip(self):
        if os.path.exists('temp/naev-package-manager'):
            shutil.rmtree('temp/naev-package-manager')
        if os.path.exists('temp/naev'):
            shutil.rmtree('temp/naev')
        if os.path.exists('temp/test.zip'):
            os.remove('temp/test.zip')
        config = TestConfig()

        shutil.copyfile('tests/test-resources/test.zip', 'temp/test.zip')

        database_connector = SqliteDatabaseConnector(config.DATABASE)
        plugin_workflow_manager = PluginWorkflowManager(database_connector, config)
        plugin = IndexedPluginDbModel(
            name='test',
            source='temp/test.zip',
            state=PluginState.INDEXED
        )
        tc = AbstractCommunication()
        plugin_workflow_manager.fetch_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.CACHED)
        # Fetching if it already exists but database is not in sync should not be a problem
        plugin.state = PluginState.INDEXED
        plugin_workflow_manager.fetch_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.CACHED)

        self.assertTrue(os.path.exists('temp/naev-package-manager/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))
        plugin_workflow_manager.install_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.INSTALLED)

        self.assertTrue(os.path.exists('temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))
        # Accept installation even if database is out of sync (plugin is installed but not marked as such)
        plugin.state = PluginState.CACHED
        plugin_workflow_manager.install_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.INSTALLED)

        self.assertTrue(os.path.exists('temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))

        plugin_workflow_manager.check_plugin(plugin, tc)
        self.assertFalse(plugin.update_available)

        # Change source file
        with open('temp/test.zip', 'w') as f:
            f.write(str(uuid.uuid4()))
        plugin_workflow_manager.check_plugin(plugin, tc)
        # Update was applied automatically with hard-linking to installation
        self.assertFalse(plugin.update_available)

        # Remove and add file again. It should be another file system node
        os.remove('temp/test.zip')
        with open('temp/test.zip', 'w') as f:
            f.write(str(uuid.uuid4()))
        plugin_workflow_manager.check_plugin(plugin, tc)
        self.assertTrue(plugin.update_available)
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/test.zip', 'temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))

        self.assertFalse(plugin.update_available)
        plugin_workflow_manager.check_plugin(plugin, tc)
        self.assertFalse(plugin.update_available)

        # Delete plugin before update check. non-existent plugin installation is treated as a plugin that can be
        # updated
        os.remove('temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip')
        plugin_workflow_manager.check_plugin(plugin, tc)
        self.assertTrue(plugin.update_available)
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/test.zip', 'temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))

        self.assertFalse(plugin.update_available)

        # Force update (although source is linked with cache and installation)
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/test.zip', 'temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))

        self.assertFalse(plugin.update_available)

        # Meddle with installation then overwrite
        with open('temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip', 'w') as f:
            f.write(str(uuid.uuid4()))
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/test.zip', 'temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))

        self.assertFalse(plugin.update_available)
        # Replace installation, then overwrite with update
        os.remove('temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip')
        with open('temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip', 'w') as f:
            f.write(str(uuid.uuid4()))
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/test.zip', 'temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))

        self.assertFalse(plugin.update_available)

        # Meddle with cache
        os.remove('temp/naev-package-manager//plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip')
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertTrue(os.path.samefile('temp/test.zip', 'temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))
        self.assertFalse(plugin.update_available)

        # Delete source and try to update -> error
        os.remove('temp/test.zip')
        try:
            plugin_workflow_manager.update_plugin(plugin, tc)
            self.assertFalse(True, 'never reach')
        except RuntimeError:
            pass

        plugin_workflow_manager.uninstall_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.CACHED)
        self.assertFalse(os.path.exists('temp/naev/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))

        # Accept inconsistency in db (already uninstalled but marked as installed):
        plugin.state = PluginState.INSTALLED
        plugin_workflow_manager.uninstall_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.CACHED)

        plugin_workflow_manager.delete_plugin(plugin, tc)
        self.assertEqual(plugin.state, PluginState.INDEXED)
        self.assertFalse(os.path.exists('temp/naev-package-manager/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))

        # Accept inconsistency in db (already deleted from cache but marked as cached):
        plugin.state = PluginState.CACHED
        plugin_workflow_manager.delete_plugin(plugin, tc)
        self.assertFalse(os.path.exists('temp/naev-package-manager/plugins/GSNFqRcI4VLA0TMyqV-nBA==_test.zip'))

        plugin_workflow_manager.remove_plugin(plugin, tc)
        self.assertIsNone(database_connector.get_plugin('temp/test.zip'))

    def test_git(self):
        if os.path.exists('temp/naev-package-manager'):
            shutil.rmtree('temp/naev-package-manager')
        if os.path.exists('temp/naev'):
            shutil.rmtree('temp/naev')
        if os.path.exists('temp/git-plugin-test'):
            shutil.rmtree('temp/git-plugin-test')
        config = TestConfig()

        shutil.copytree('tests/test-resources/git-plugin-test', 'temp/git-plugin-test')

        database_connector = SqliteDatabaseConnector(config.DATABASE)
        plugin_workflow_manager = PluginWorkflowManager(database_connector, config)
        plugin = IndexedPluginDbModel(
            name='test',
            source='temp/git-plugin-test/',
            state=PluginState.INDEXED
        )
        tc = AbstractCommunication()
        plugin_workflow_manager.fetch_plugin(plugin, tc)
        self.assertTrue(os.path.exists('temp/naev-package-manager/plugins/FrZf0W4ltapGH-HPlQtTrg==_test'))
        plugin_workflow_manager.install_plugin(plugin, tc)
        self.assertTrue(os.path.exists('temp/naev/plugins/FrZf0W4ltapGH-HPlQtTrg==_test'))
        plugin_workflow_manager.check_plugin(plugin, tc)
        self.assertFalse(plugin.update_available)
        with open('temp/git-plugin-test/test.txt', 'w') as f:
            f.write(str(uuid.uuid4()))
        repo = pygit2.Repository('temp/git-plugin-test/')
        index = repo.index
        index.add('test.txt')
        index.write()
        ref = "HEAD"
        author = pygit2.Signature('test', 'dummy@mail.address')
        committer = pygit2.Signature('test', 'dummy@mail.address')
        message = "Add 'temp/git-plugin-test/test.txt'"
        tree = index.write_tree()
        parents = [repo.head.target]
        repo.create_commit(ref, author, committer, message, tree, parents)
        plugin_workflow_manager.check_plugin(plugin, tc)
        self.assertTrue(plugin.update_available)
        plugin_workflow_manager.update_plugin(plugin, tc)
        self.assertFalse(plugin.update_available)
        plugin_workflow_manager.uninstall_plugin(plugin, tc)
        self.assertFalse(os.path.exists('temp/naev/plugins/FrZf0W4ltapGH-HPlQtTrg==_test'))
        plugin_workflow_manager.delete_plugin(plugin, tc)
        self.assertFalse(os.path.exists('temp/naev-package-manager/plugins/FrZf0W4ltapGH-HPlQtTrg==_test'))
