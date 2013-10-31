import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import ModifyFields
import Utils

class TestModifyFields(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestModifyFields, self).setUp(ModifyFields.ModifyFields(gp=mock.Mock()))
        self.default_dict = Utils.getDefaultDataDict({})

    def testDelete(self):
        self.default_dict['delme'] = 1
        self.test_object.configure({'action': 'delete',
                                    'source_fields': ['delme']})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('delme' not in result)

    def testReplaceStatic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.test_object.configure({'action': 'replace',
                                    'source_field': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': 'English'})
        result = self.test_object.handleData(self.default_dict)
        self.assertEquals(result['replaceme'], 'The English Inquisition')

    def testReplaceDynamic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.default_dict['withme'] = 'English'
        self.test_object.configure({'action': 'replace',
                                    'source_field': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': '%(withme)s'})
        result = self.test_object.handleData(self.default_dict)
        self.assertEquals(result['replaceme'], 'The English Inquisition')

    def testMap(self):
        self.default_dict['http_status'] = 100
        self.test_object.configure({'action': 'map',
                                    'source_field': 'http_status',
                                    'map': {100: 'Continue',
                                            200: 'OK'}
                                  })
        result = self.test_object.handleData(self.default_dict)
        self.assert_('http_status_mapped' in result)
        self.assertEquals(result['http_status_mapped'], 'Continue')

    def testMapWithTargetField(self):
        self.default_dict['http_status'] = 200
        self.test_object.configure({'action': 'map',
                                    'source_field': 'http_status',
                                    'map': {100: 'Continue',
                                            200: 'OK'},
                                    'target_field': 'http_status'
                                  })
        result = self.test_object.handleData(self.default_dict)
        self.assertEquals(result['http_status'], 'OK')

    def testKeep(self):
        self.default_dict['keep-this'] = 'The Spanish Inquisition'
        self.default_dict['keep-that'] = 'My hovercraft is full of eels!'
        self.default_dict['drop-this'] = 'English'
        self.test_object.configure({'action': 'keep',
                                    'source_fields': ['keep-this','keep-that']})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('keep-this' in result and 'keep-that' in result and 'drop-this' not in result)

    def testCastToInteger(self):
        self.default_dict['castable'] = '3'
        self.default_dict['non-castable'] = 'Three shall be the number thou shalt count, and the number of the counting shall be three.'
        self.test_object.configure({'action': 'castToInteger',
                                    'source_fields': ['castable','non-castable', 'not-existing']})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('castable' in result and result['castable'] == 3)
        self.assertTrue('non-castable' in result and result['non-castable'] == 0)

    def testCastToFloat(self):
        self.default_dict['castable'] = '3.0'
        self.default_dict['non-castable'] = 'Three shall be the number thou shalt count, and the number of the counting shall be three.'
        self.test_object.configure({'action': 'castToFloat',
                                    'source_fields': ['castable','non-castable', 'not-existing']})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('castable' in result and result['castable'] == 3.0)
        self.assertTrue('non-castable' in result and result['non-castable'] == 0)

    def testCastToString(self):
        self.default_dict['castable'] = 3.1415
        self.test_object.configure({'action': 'castToString',
                                    'source_fields': ['castable', 'not-existing']})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('castable' in result and result['castable'] == "3.1415")

    def testCastToBoolean(self):
        self.default_dict['castable'] = 'True'
        self.test_object.configure({'action': 'castToBoolean',
                                    'source_fields': ['castable', 'not-existing']})
        result = self.test_object.handleData(self.default_dict)
        self.assertTrue('castable' in result and result['castable'] == True)

    def testQueueCommunication(self):
        config = {'source_fields': ['data'],
                  'action': 'keep'  }
        super(TestModifyFields, self).testQueueCommunication(config)

    def testOutputQueueFilterNoMatch(self):
        config = {'source_fields': ['data'],
                  'action': 'keep'  }
        super(TestModifyFields, self).testOutputQueueFilterNoMatch(config)

    def testOutputQueueFilterMatch(self):
        config = {'source_fields': ['data', 'Johann'],
                  'action': 'keep'  }
        super(TestModifyFields, self).testOutputQueueFilterMatch(config)

    def testWorksOnCopy(self):
        config = {'source_fields': ['data'],
                  'action': 'keep'  }
        super(TestModifyFields, self).testWorksOnCopy(config)

    def testWorksOnOriginal(self):
        config = {'source_fields': ['data'],
                  'action': 'keep'  }
        super(TestModifyFields, self).testWorksOnOriginal(config)

if __name__ == '__main__':
    unittest.main()