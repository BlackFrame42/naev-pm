import os
import shutil
import unittest
from naevpm.core.application_logic import ApplicationLogic
from naevpm.core.config import Config
from naevpm.core.sqlite_database_connector import SqliteDatabaseConnector


class TestConfig(Config):
    def __init__(self, ):
        super().__init__("temp/naev-package-manager", "temp/naev")


class TestSqliteDatabaseConnector(unittest.TestCase):

    def test_plugin_metadata(self):
        if os.path.exists('temp/naev-package-manager'):
            shutil.rmtree('temp/naev-package-manager')
        if os.path.exists('temp/naev'):
            shutil.rmtree('temp/naev')

        config = TestConfig()

        sqlite_data_connector = SqliteDatabaseConnector(config.DATABASE)
        no_plugin_metadata = sqlite_data_connector.get_plugin_metadata('temp/test-resources/git-plugin-test')
        self.assertIsNone(no_plugin_metadata)

        application_logic = ApplicationLogic(sqlite_data_connector, config)
        read_plugin_metadata = application_logic._parse_plugin_metadata_xml_file(
            'tests/test-resources/git-plugin-test/plugin.xml')

        self.assertEqual(read_plugin_metadata.name, 'Test Plugin')
        self.assertEqual(read_plugin_metadata.version, '0.1')
        self.assertEqual(read_plugin_metadata.description, 'Test descritpion test description')
        self.assertEqual(read_plugin_metadata.compatibility, 'woeifj weoifj ')
        self.assertEqual(read_plugin_metadata.priority, 2)
        self.assertEqual(read_plugin_metadata.source, 'temp/test-resources/git-plugin-test')
        self.assertEqual(read_plugin_metadata.blacklist, ['asdf', 'asdf2'])
        self.assertEqual(read_plugin_metadata.whitelist, ['weoine', 'weoine2'])
        self.assertTrue(read_plugin_metadata.total_conversion)

        sqlite_data_connector.insert_plugin_metadata(read_plugin_metadata)

        db_plugin_metadata = sqlite_data_connector.get_plugin_metadata('temp/test-resources/git-plugin-test')

        self.assertEqual(db_plugin_metadata.name, 'Test Plugin')
        self.assertEqual(db_plugin_metadata.version, '0.1')
        self.assertEqual(db_plugin_metadata.description, 'Test descritpion test description')
        self.assertEqual(db_plugin_metadata.compatibility, 'woeifj weoifj ')
        self.assertEqual(db_plugin_metadata.priority, 2)
        self.assertEqual(db_plugin_metadata.source, 'temp/test-resources/git-plugin-test')
        self.assertEqual(db_plugin_metadata.blacklist, ['asdf', 'asdf2'])
        self.assertEqual(db_plugin_metadata.whitelist, ['weoine', 'weoine2'])
        self.assertTrue(db_plugin_metadata.total_conversion)
