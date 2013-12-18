import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import ModifyFields
import Utils

class TestModifyFields(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestModifyFields, self).setUp(ModifyFields.ModifyFields(gp=mock.Mock()))
        self.default_dict = Utils.getDefaultEventDict({})

    def testDelete(self):
        self.default_dict['delme'] = 1
        self.test_object.configure({'action': 'delete',
                                    'source_fields': ['delme']})
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assertTrue('delme' not in event)

    def testConcat(self):
        self.default_dict['First name'] = 'Johann'
        self.default_dict['Last name'] = 'Gambolputty'
        self.test_object.configure({'action': 'concat',
                                    'source_fields': ['First name', 'Last name'],
                                    'target_field': 'Name'})
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assertTrue('Name' in event and event['Name'] == 'JohannGambolputty')

    def testInsert(self):
        self.default_dict['First name'] = 'Johann'
        self.default_dict['Last name'] = 'Gambolputty'
        self.test_object.configure({'action': 'insert',
                                    'value': "%(First name)s %(Last name)s de von Ausfern",
                                    'target_field': 'Name'})
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assertTrue('Name' in event and event['Name'] == 'Johann Gambolputty de von Ausfern')

    def testReplaceStatic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.test_object.configure({'action': 'replace',
                                    'source_field': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': 'English'})
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assertEquals(event['replaceme'], 'The English Inquisition')

    def testReplaceDynamic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.default_dict['withme'] = 'English'
        self.test_object.configure({'action': 'replace',
                                    'source_field': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': '%(withme)s'})
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assertEquals(event['replaceme'], 'The English Inquisition')

    def testMap(self):
        self.default_dict['http_status'] = 100
        self.test_object.configure({'action': 'map',
                                    'source_field': 'http_status',
                                    'map': {100: 'Continue',
                                            200: 'OK'}
                                  })
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assert_('http_status_mapped' in event)
            self.assertEquals(event['http_status_mapped'], 'Continue')

    def testMapWithTargetField(self):
        self.default_dict['http_status'] = 200
        self.test_object.configure({'action': 'map',
                                    'source_field': 'http_status',
                                    'map': {100: 'Continue',
                                            200: 'OK'},
                                    'target_field': 'http_status'
                                  })
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assertEquals(event['http_status'], 'OK')

    def testKeep(self):
        self.default_dict['keep-this'] = 'The Spanish Inquisition'
        self.default_dict['keep-that'] = 'My hovercraft is full of eels!'
        self.default_dict['drop-this'] = 'English'
        self.test_object.configure({'action': 'keep',
                                    'source_fields': ['keep-this','keep-that']})
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assertTrue('keep-this' in event and 'keep-that' in event and 'drop-this' not in event)

    def testCastToInteger(self):
        self.default_dict['castable'] = '3'
        self.default_dict['non-castable'] = 'Three shall be the number thou shalt count, and the number of the counting shall be three.'
        self.test_object.configure({'action': 'castToInteger',
                                    'source_fields': ['castable','non-castable', 'not-existing']})
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assertTrue('castable' in event and event['castable'] == 3)
            self.assertTrue('non-castable' in event and event['non-castable'] == 0)

    def testCastToFloat(self):
        self.default_dict['castable'] = '3.0'
        self.default_dict['non-castable'] = 'Three shall be the number thou shalt count, and the number of the counting shall be three.'
        self.test_object.configure({'action': 'castToFloat',
                                    'source_fields': ['castable','non-castable', 'not-existing']})
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assertTrue('castable' in event and event['castable'] == 3.0)
            self.assertTrue('non-castable' in event and event['non-castable'] == 0)

    def testCastToString(self):
        self.default_dict['castable'] = 3.1415
        self.test_object.configure({'action': 'castToString',
                                    'source_fields': ['castable', 'not-existing']})
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assertTrue('castable' in event and event['castable'] == "3.1415")

    def testCastToBoolean(self):
        self.default_dict['castable'] = 'True'
        self.test_object.configure({'action': 'castToBoolean',
                                    'source_fields': ['castable', 'not-existing']})
        self.test_object.handleEvent(self.default_dict)
        for event in self.receiver.getEvent():
            self.assertTrue('castable' in event and event['castable'] == True)

    def testReplaceFieldValueWithMd5Hash(self):
        self.test_object.configure({'action': 'hash',
                                    'source_fields': ['hash_me']})
        expected = Utils.getDefaultEventDict({'hash_me': 'bb649c83dd1ea5c9d9dec9a18df0ffe9'})
        self.test_object.handleEvent(Utils.getDefaultEventDict({'hash_me': 'Nobody inspects the spammish repetition'}))
        for event in self.receiver.getEvent():
            self.assertEqual(event, expected)

    def testMd5Hash(self):
        self.test_object.configure({'action': 'hash',
                                    'source_fields': ['hash_me'],
                                    'target_fields': ['hash_me_hashed']})
        expected = Utils.getDefaultEventDict({'hash_me': 'Nobody inspects the spammish repetition', 'hash_me_hashed': 'bb649c83dd1ea5c9d9dec9a18df0ffe9'})
        self.test_object.handleEvent(Utils.getDefaultEventDict({'hash_me': 'Nobody inspects the spammish repetition'}))
        for event in self.receiver.getEvent():
            self.assertEqual(event, expected)

    def testSha1Hash(self):
        self.test_object.configure({'action': 'hash',
                                    'algorithm': 'sha1',
                                    'source_fields': ['hash_me'],
                                    'target_fields': ['hash_me_hashed']})
        expected = Utils.getDefaultEventDict({'hash_me': 'Nobody inspects the spammish repetition', 'hash_me_hashed': '531b07a0f5b66477a21742d2827176264f4bbfe2'})
        self.test_object.handleEvent(Utils.getDefaultEventDict({'hash_me': 'Nobody inspects the spammish repetition'}))
        for event in self.receiver.getEvent():
            self.assertEqual(event, expected)

    def testAnonymize(self):
        self.test_object.configure({'action': 'anonymize',
                                    'source_fields': ['anon_me']})
        expected = Utils.getDefaultEventDict({'anon_me': 'bb649c83dd1ea5c9d9dec9a18df0ffe9'})
        self.test_object.handleEvent(Utils.getDefaultEventDict({'anon_me': 'Nobody inspects the spammish repetition'}))
        for event in self.receiver.getEvent():
            self.assertEqual(event, expected)


    def __testQueueCommunication(self):
        config = {'source_fields': ['data'],
                  'action': 'keep'  }
        super(TestModifyFields, self).testQueueCommunication(config)

    def __testOutputQueueFilterNoMatch(self):
        config = {'source_fields': ['data'],
                  'action': 'keep'  }
        super(TestModifyFields, self).testOutputQueueFilterNoMatch(config)

    def __testOutputQueueFilterMatch(self):
        config = {'source_fields': ['data', 'Johann'],
                  'action': 'keep'  }
        super(TestModifyFields, self).testOutputQueueFilterMatch(config)

if __name__ == '__main__':
    unittest.main()