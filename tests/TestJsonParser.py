import ModuleBaseTestCase
import mock
import json


import lumbermill.utils.DictUtils as DictUtils
from lumbermill.parser import JsonParser


class TestJsonParser(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestJsonParser, self).setUp(JsonParser.JsonParser(mock.Mock()))

    def testDecode(self):
        self.test_object.configure({'source_fields': ['json_data']})
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'json_data': '{"South African": "Fast", "unladen": "swallow"}'})
        event = None
        for event in self.test_object.handleEvent(data):
            self.assertTrue('South African' in event and event['South African'] == "Fast")
        self.assertIsNotNone(event)

    def testEncode(self):
        self.test_object.configure({'action': 'encode',
                                    'source_fields': 'all',
                                    'target_field': 'json_data'})
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({"South African": "Fast", "unladen": "swallow"})
        event = None
        for event in self.test_object.handleEvent(data):
            json_str = event.pop('json_data')
            self.assertDictEqual(json.loads(json_str), data)
        self.assertIsNotNone(event)
