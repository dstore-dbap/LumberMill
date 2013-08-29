import extendSysPath
import unittest
import ModifyField
import Utils

class TestModifyField(unittest.TestCase):
    def setUp(self):
        self.test_object = ModifyField.ModifyField()
        self.default_dict = Utils.getDefaultDataDict({})
        
    def testDelete(self):
        self.default_dict['delme'] = 1
        self.test_object.configure({'action': 'delete',
                                    'field': 'delme'})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('delme' not in result)

    def testReplaceStatic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.test_object.configure({'action': 'replaceStatic',
                                    'field': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': 'English'})
        result = self.test_object.handleData(self.default_dict)
        self.assertEquals(result['replaceme'], 'The English Inquisition')

    def testReplaceDynamic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.default_dict['withme'] = 'English'
        self.test_object.configure({'action': 'replaceDynamic',
                                    'field': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': 'withme'})
        result = self.test_object.handleData(self.default_dict)
        self.assertEquals(result['replaceme'], 'The English Inquisition')
    
if __name__ == '__main__':
    unittest.main()