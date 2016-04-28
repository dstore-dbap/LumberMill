import ModuleBaseTestCase
import mock

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.parser import LineParser


class TestLineParser(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestLineParser, self).setUp(LineParser.LineParser(mock.Mock()))

    def testLineParserWithSourceAndTargetField(self):
        config = {'seperator': ' ',
                  'source_field': 'splitme',
                  'target_field': 'splitted',
                  'keep_original': False}
        self.test_object.configure(config)
        self.checkConfiguration()
        payload = "Venezuelan beaver cheese?"
        data = DictUtils.getDefaultEventDict({'splitme': payload})
        expected_result = ['Venezuelan', 'beaver', 'cheese?']
        for event in self.test_object.handleEvent(data):
            self.assertTrue(event['splitted'] == expected_result)

    def tearDown(self):
        pass