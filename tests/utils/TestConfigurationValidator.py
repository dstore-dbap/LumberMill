import unittest
import yaml
import sys

from lumbermill.constants import LUMBERMILL_BASEPATH
from lumbermill.utils.ConfigurationValidator import ConfigurationValidator


class TestConfigurationValidator(unittest.TestCase):

    def readConfigurationData(self, path_to_config_file):
        try:
            with open(path_to_config_file, "r") as configuration_file:
                raw_conf_file = configuration_file.read()
            return yaml.safe_load(raw_conf_file)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not read config file %s. Exception: %s, Error: %s." % (path_to_config_file, etype, evalue))
            raise

    def testValidSimpleConfiguration(self):
        configuration = self.readConfigurationData(LUMBERMILL_BASEPATH + "/../tests/test_data/conf_examples/simple.conf")
        configuration_errors = ConfigurationValidator().validateConfiguration(configuration)
        self.assertEqual(len(configuration_errors), 0)

    def testInvalidSimpleConfiguration(self):
        configuration = self.readConfigurationData(LUMBERMILL_BASEPATH + "/../tests/test_data/conf_examples/simple_invalid.conf")
        configuration_errors = ConfigurationValidator().validateConfiguration(configuration)
        expected_errors = ["'Global.workers' not of correct datatype. Is: <type 'str'>, should be: [<type 'int'>]. Please check your configuration.",
                           "'Spam' not of correct datatype. Is: <type 'int'>, should be: [<type 'dict'>, <type 'str'>]. Please check your configuration.",
                           "'Spam.filter' not of correct datatype. Is: <type 'int'>, should be: [<type 'str'>]. Please check your configuration.",
                           "'Spam.add_fields' not of correct datatype. Is: <type 'list'>, should be: [<type 'dict'>]. Please check your configuration.",
                           "'Spam.id' not of correct datatype. Is: <type 'bool'>, should be: [<type 'str'>]. Please check your configuration.",
                           "'Spam.delete_fields' not of correct datatype. Is: <type 'int'>, should be: [<type 'list'>]. Please check your configuration.",
                           "'Spam.receivers' not of correct datatype. Is: <type 'str'>, should be: [<type 'list'>]. Please check your configuration."]
        self.assertEqual(configuration_errors.sort(), expected_errors.sort())