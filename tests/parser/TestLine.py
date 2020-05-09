import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.parser import Line


class TestLine(ModuleBaseTestCase):

    def setUp(self):
        super(TestLine, self).setUp(Line.Line(mock.Mock()))

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
