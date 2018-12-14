import mock
import re
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.modifier import AddDateTime


class TestAddDateTime(ModuleBaseTestCase):

    def setUp(self):
        super(TestAddDateTime, self).setUp(AddDateTime.AddDateTime(mock.Mock()))

    def testIsTimeStamp(self):
        self.test_object.configure({})
        self.checkConfiguration()
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({})):
            self.assert_(re.match('^\d+-\d+-\d+T\d+:\d+:\d+$', event['@timestamp'])) # 2013-08-29T10:25:26

    def testAddDateTimeCustomFormat(self):
        self.test_object.configure({'target_format': '%Y/%M/%d %H.%M.%S'})
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({})):
            self.assert_(re.match('^\d+/\d+/\d+ \d+.\d+.\d+$', event['@timestamp'])) # 2013/08/29 10.25.26

    def testAddDateTimeDefaultField(self):
        self.test_object.configure({})
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({})):
            self.assert_('@timestamp' in event)

    def testAddDateTimeCustomFieldtestAddDateTimeCustomField(self):
        self.test_object.configure({'target_field': 'test'})
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({})):
            self.assert_('test' in event)

    def testAddDateTimeFromSourceField(self):
        self.test_object.configure({'source_fields': ['timestamp'],
                                    'source_formats': ['%Y', '%Y-%m-%dT%H:%M:%S.%fZ']})
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({'timestamp': '2018-11-07T10:05:07.431Z'})): # -11-07T10:05:07.431Z
            self.assertTrue('@timestamp' in event)
            self.assertEqual(event['@timestamp'], '2018-11-07T10:05:07')