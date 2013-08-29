import extendSysPath
import unittest
import re
import Utils
import AddDateTime

class TestAddDateTime(unittest.TestCase):
    def setUp(self):
        self.test_object = AddDateTime.AddDateTime()
        self.default_dict = Utils.getDefaultDataDict({})

    def testIsTimeStamp(self):
        self.test_object.configure({})
        dict_with_date = self.test_object.handleData(self.default_dict)
        self.assert_(re.match('^\d+-\d+-\d+T\d+:\d+:\d+$', dict_with_date['@timestamp'])) # 2013-08-29T10:25:26
    
    def testAddDateTimeDefaultField(self):
        self.test_object.configure({})
        dict_with_date = self.test_object.handleData(self.default_dict)
        self.assert_('@timestamp' in dict_with_date)

    def testAddDateTimeCustomField(self):
        self.test_object.configure({'field': 'test'})
        dict_with_date = self.test_object.handleData(self.default_dict)
        self.assert_('test' in dict_with_date)
      
    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()