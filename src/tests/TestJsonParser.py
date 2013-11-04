import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import re
import Utils
import JsonParser

class TestJsonParser(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestJsonParser, self).setUp(JsonParser.JsonParser(gp=mock.Mock()))

    def testSimpleJson(self):
        self.test_object.configure({'source_field': 'json_data'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        data = Utils.getDefaultDataDict({'json_data': "'{\"South African\": \"Fast\", \"unladen\": \"Swallow\"}'"})
        for result in self.test_object.handleData(data):
            self.assertTrue('South African' in result and result['South African'] == "Fast" )

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()