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
        for result in self.test_object.handleData(self.default_dict):
            self.assertTrue('delme' not in result)

    def testConcat(self):
        self.default_dict['First name'] = 'Johann'
        self.default_dict['Last name'] = 'Gambolputty'
        self.test_object.configure({'action': 'concat',
                                    'source_fields': ['First name', 'Last name'],
                                    'target_field': 'Name'})
        for result in self.test_object.handleData(self.default_dict):
            self.assertTrue('Name' in result and result['Name'] == 'JohannGambolputty')

    def testInsert(self):
        self.default_dict['First name'] = 'Johann'
        self.default_dict['Last name'] = 'Gambolputty'
        self.test_object.configure({'action': 'insert',
                                    'value': "%(First name)s %(Last name)s de von Ausfern",
                                    'target_field': 'Name'})
        for result in self.test_object.handleData(self.default_dict):
            self.assertTrue('Name' in result and result['Name'] == 'Johann Gambolputty de von Ausfern')

    def testReplaceStatic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.test_object.configure({'action': 'replace',
                                    'source_field': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': 'English'})
        for result in self.test_object.handleData(self.default_dict):
            self.assertEquals(result['replaceme'], 'The English Inquisition')

    def testReplaceDynamic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.default_dict['withme'] = 'English'
        self.test_object.configure({'action': 'replace',
                                    'source_field': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': '%(withme)s'})
        for result in self.test_object.handleData(self.default_dict):
            self.assertEquals(result['replaceme'], 'The English Inquisition')

    def testMap(self):
        self.default_dict['http_status'] = 100
        self.test_object.configure({'action': 'map',
                                    'source_field': 'http_status',
                                    'map': {100: 'Continue',
                                            200: 'OK'}
                                  })
        for result in self.test_object.handleData(self.default_dict):
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
        for result in self.test_object.handleData(self.default_dict):
            self.assertEquals(result['http_status'], 'OK')

    def testKeep(self):
        self.default_dict['keep-this'] = 'The Spanish Inquisition'
        self.default_dict['keep-that'] = 'My hovercraft is full of eels!'
        self.default_dict['drop-this'] = 'English'
        self.test_object.configure({'action': 'keep',
                                    'source_fields': ['keep-this','keep-that']})
        for result in self.test_object.handleData(self.default_dict):
            self.assertTrue('keep-this' in result and 'keep-that' in result and 'drop-this' not in result)

    def testCastToInteger(self):
        self.default_dict['castable'] = '3'
        self.default_dict['non-castable'] = 'Three shall be the number thou shalt count, and the number of the counting shall be three.'
        self.test_object.configure({'action': 'castToInteger',
                                    'source_fields': ['castable','non-castable', 'not-existing']})
        for result in self.test_object.handleData(self.default_dict):
            self.assertTrue('castable' in result and result['castable'] == 3)
            self.assertTrue('non-castable' in result and result['non-castable'] == 0)

    def testCastToFloat(self):
        self.default_dict['castable'] = '3.0'
        self.default_dict['non-castable'] = 'Three shall be the number thou shalt count, and the number of the counting shall be three.'
        self.test_object.configure({'action': 'castToFloat',
                                    'source_fields': ['castable','non-castable', 'not-existing']})
        for result in self.test_object.handleData(self.default_dict):
            self.assertTrue('castable' in result and result['castable'] == 3.0)
            self.assertTrue('non-castable' in result and result['non-castable'] == 0)

    def testCastToString(self):
        self.default_dict['castable'] = 3.1415
        self.test_object.configure({'action': 'castToString',
                                    'source_fields': ['castable', 'not-existing']})
        for result in self.test_object.handleData(self.default_dict):
            self.assertTrue('castable' in result and result['castable'] == "3.1415")

    def testCastToBoolean(self):
        self.default_dict['castable'] = 'True'
        self.test_object.configure({'action': 'castToBoolean',
                                    'source_fields': ['castable', 'not-existing']})
        for result in self.test_object.handleData(self.default_dict):
            self.assertTrue('castable' in result and result['castable'] == True)

    def testReplaceFieldValueWithMd5Hash(self):
        self.test_object.configure({'action': 'hash',
                                    'source_fields': ['hash_me']})
        expected = Utils.getDefaultDataDict({'hash_me': 'bb649c83dd1ea5c9d9dec9a18df0ffe9'})
        for result in self.test_object.handleData(Utils.getDefaultDataDict({'hash_me': 'Nobody inspects the spammish repetition'})):
            self.assertEqual(result, expected)

    def testMd5Hash(self):
        self.test_object.configure({'action': 'hash',
                                    'source_fields': ['hash_me'],
                                    'target_fields': ['hash_me_hashed']})
        expected = Utils.getDefaultDataDict({'hash_me': 'Nobody inspects the spammish repetition', 'hash_me_hashed': 'bb649c83dd1ea5c9d9dec9a18df0ffe9'})
        for result in self.test_object.handleData(Utils.getDefaultDataDict({'hash_me': 'Nobody inspects the spammish repetition'})):
            self.assertEqual(result, expected)

    def testSha1Hash(self):
        self.test_object.configure({'action': 'hash',
                                    'algorithm': 'sha1',
                                    'source_fields': ['hash_me'],
                                    'target_fields': ['hash_me_hashed']})
        expected = Utils.getDefaultDataDict({'hash_me': 'Nobody inspects the spammish repetition', 'hash_me_hashed': '531b07a0f5b66477a21742d2827176264f4bbfe2'})
        for result in self.test_object.handleData(Utils.getDefaultDataDict({'hash_me': 'Nobody inspects the spammish repetition'})):
            self.assertEqual(result, expected)

    def testAnonymize(self):
        self.test_object.configure({'action': 'anonymize',
                                    'source_fields': ['anon_me']})
        expected = Utils.getDefaultDataDict({'anon_me': 'bb649c83dd1ea5c9d9dec9a18df0ffe9'})
        for result in self.test_object.handleData(Utils.getDefaultDataDict({'anon_me': 'Nobody inspects the spammish repetition'})):
            print result
            self.assertEqual(result, expected)


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

if __name__ == '__main__':
    unittest.main()