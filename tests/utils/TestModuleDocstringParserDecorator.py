import unittest
import logging

from lumbermill.utils.Decorators import ModuleDocstringParser

@ModuleDocstringParser
class DocStringExample:
    """
    - module: DocStringExample
       string:                           # <default: "TestString"; type: string; is: optional>
       int:                              # <default: 1; type: integer; is: optional>
       dict:                             # <default: {'filed1': 'value1'}; type: dict; is: optional>
       list:                             # <default: ['field2', 'field3']; type: list; is: optional>
       none:                             # <default: None; type: None||string; is: optional>
       bool:                             # <default: True; type: boolean; is: optional>
       ...
       receivers:
        - ModuleName
        - ModuleAlias
    """

    def __init__(self):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            filename=None,
                            filemode='w')
        self.logger = logging.getLogger(self.__class__.__name__)
        self.configuration_data = {}

class TestModuleDocStringParserDecorator(unittest.TestCase):

    def testConfigurationData(self):
        self.doc_string_example = DocStringExample()
        doc_string_config_data = self.doc_string_example.configuration_data
        self.assertEquals(doc_string_config_data['string'], "TestString")
        self.assertEquals(doc_string_config_data['int'], 1)
        self.assertEquals(doc_string_config_data['dict'], {'filed1': 'value1'})
        self.assertEquals(doc_string_config_data['list'], ['field2', 'field3'])
        self.assertEquals(doc_string_config_data['none'], None)
        self.assertEquals(doc_string_config_data['bool'], True)




