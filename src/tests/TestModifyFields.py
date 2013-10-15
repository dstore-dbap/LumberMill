import extendSysPath
import unittest
import Queue
import ModifyFields
import Utils

class TestModifyFields(unittest.TestCase):
    def setUp(self):
        self.input_queue = Queue.Queue()
        self.output_queue = Queue.Queue()
        self.test_object = ModifyFields.ModifyFields()
        self.test_object.setup()
        self.default_dict = Utils.getDefaultDataDict({})
        self.test_object.setInputQueue(self.input_queue)
        self.test_object.addOutputQueue(self.output_queue, filter_by_marker=False, filter_by_field=False)

    def testDelete(self):
        self.default_dict['delme'] = 1
        self.test_object.configure({'action': 'delete',
                                    'fields': 'delme'})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('delme' not in result)

    def testReplaceStatic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.test_object.configure({'action': 'replaceStatic',
                                    'fields': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': 'English'})
        result = self.test_object.handleData(self.default_dict)
        self.assertEquals(result['replaceme'], 'The English Inquisition')

    def testReplaceDynamic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.default_dict['withme'] = 'English'
        self.test_object.configure({'action': 'replaceDynamic',
                                    'fields': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': 'withme'})
        result = self.test_object.handleData(self.default_dict)
        self.assertEquals(result['replaceme'], 'The English Inquisition')

    def testMap(self):
        self.default_dict['http_status'] = 100
        self.test_object.configure({'action': 'map',
                                    'fields': 'http_status',
                                    'with': {100: 'Continue',
                                             200: 'OK'
                                        }
                                  })
        result = self.test_object.handleData(self.default_dict)
        self.assertEquals(result['http_status_mapped'], 'Continue')

    def testTranslateWithTargetField(self):
        self.default_dict['http_status'] = 200
        self.test_object.configure({'action': 'map',
                                    'fields': 'http_status',
                                    'with': {100: 'Continue',
                                             200: 'OK'
                                        },
                                    'target_field': 'http_status'
                                  })
        result = self.test_object.handleData(self.default_dict)
        self.assertEquals(result['http_status'], 'OK')

    def testKeep(self):
        self.default_dict['keep-this'] = 'The Spanish Inquisition'
        self.default_dict['keep-that'] = 'My hovercraft is full of eels!'
        self.default_dict['drop-this'] = 'English'
        self.test_object.configure({'action': 'keep',
                                    'fields': ['keep-this','keep-that']})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('keep-this' in result and 'keep-that' in result and 'drop-this' not in result)

    def testCastToInteger(self):
        self.default_dict['castable'] = '3'
        self.default_dict['non-castable'] = 'Three shall be the number thou shalt count, and the number of the counting shall be three.'
        self.test_object.configure({'action': 'castToInteger',
                                    'fields': ['castable','non-castable', 'not-existing']})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('castable' in result and result['castable'] == 3)
        self.assertTrue('non-castable' in result and result['non-castable'] == 0)

    def testCastToFloat(self):
        self.default_dict['castable'] = '3.0'
        self.default_dict['non-castable'] = 'Three shall be the number thou shalt count, and the number of the counting shall be three.'
        self.test_object.configure({'action': 'castToFloat',
                                    'fields': ['castable','non-castable', 'not-existing']})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('castable' in result and result['castable'] == 3.0)
        self.assertTrue('non-castable' in result and result['non-castable'] == 0)

    def testCastToString(self):
        self.default_dict['castable'] = 3.1415
        self.test_object.configure({'action': 'castToString',
                                    'fields': ['castable', 'not-existing']})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('castable' in result and result['castable'] == "3.1415")

    def testCastToBoolean(self):
        self.default_dict['castable'] = 'True'
        self.test_object.configure({'action': 'castToBoolean',
                                    'fields': ['castable', 'not-existing']})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('castable' in result and result['castable'] == True)

if __name__ == '__main__':
    unittest.main()