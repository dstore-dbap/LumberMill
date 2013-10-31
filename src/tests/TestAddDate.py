import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import re
import Utils
import AddDateTime

class TestAddDateTime(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestAddDateTime, self).setUp(AddDateTime.AddDateTime(gp=mock.Mock()))

    def testIsTimeStamp(self):
        self.test_object.configure({})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        dict_with_date = self.test_object.handleData(Utils.getDefaultDataDict({}))
        self.assert_(re.match('^\d+-\d+-\d+T\d+:\d+:\d+$', dict_with_date['@timestamp'])) # 2013-08-29T10:25:26

    def testAddDateTimeCustomFormat(self):
        self.test_object.configure({'format': '%Y/%M/%d %H.%M.%S'})
        dict_with_date = self.test_object.handleData(Utils.getDefaultDataDict({}))
        self.assert_(re.match('^\d+/\d+/\d+ \d+.\d+.\d+$', dict_with_date['@timestamp'])) # 2013/08/29 10.25.26

    def testAddDateTimeDefaultField(self):
        self.test_object.configure({})
        dict_with_date = self.test_object.handleData(Utils.getDefaultDataDict({}))
        self.assert_('@timestamp' in dict_with_date)

    def testAddDateTimeCustomField(self):
        self.test_object.configure({'target_field': 'test'})
        dict_with_date = self.test_object.handleData(Utils.getDefaultDataDict({}))
        self.assert_('test' in dict_with_date)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()