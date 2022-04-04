import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.modifier import Field


class TestFields(ModuleBaseTestCase):

    def setUp(self):
        super(TestFields, self).setUp(Field.Field(mock.Mock()))
        self.default_dict = DictUtils.getDefaultEventDict({})

    def testDelete(self):
        self.default_dict['delme'] = 1
        self.default_dict['nested'] = {'delme': 1}
        self.test_object.configure({'action': 'delete',
                                    'source_fields': ['delme','nested.delme']})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertTrue('delme' not in event)

    def testConcat(self):
        self.default_dict['First name'] = 'Johann'
        self.default_dict['Last name'] = 'Gambolputty'
        self.test_object.configure({'action': 'concat',
                                    'source_fields': ['First name', 'Last name'],
                                    'target_field': 'Name'})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertTrue('Name' in event and event['Name'] == 'JohannGambolputty')

    def testUpper(self):
        self.default_dict['First name'] = 'Johann'
        self.default_dict['Last name'] = 'Gambolputty'
        self.test_object.configure({'action': 'upper',
                                    'source_fields': ['First name', 'Last name']})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertTrue('First name' in event and event['First name'] == 'JOHANN')
            self.assertTrue('Last name' in event and event['Last name'] == 'GAMBOLPUTTY')

    def testLowerWithTargetFields(self):
        self.default_dict['First name'] = 'Johann'
        self.default_dict['Last name'] = 'Gambolputty'
        self.test_object.configure({'action': 'lower',
                                    'source_fields': ['First name', 'Last name'],
                                    'target_fields': ['First name lower', 'Last name lower']})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertTrue('First name lower' in event and event['First name lower'] == 'johann')
            self.assertTrue('Last name lower' in event and event['Last name lower'] == 'gambolputty')

    def testInsert(self):
        self.default_dict['First name'] = 'Johann'
        self.default_dict['Last name'] = 'Gambolputty'
        self.test_object.configure({'action': 'insert',
                                    'value': "$(First name) $(Last name) de von Ausfern",
                                    'target_field': 'Name'})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertTrue('Name' in event and event['Name'] == 'Johann Gambolputty de von Ausfern')

    def testSlice(self):
        self.default_dict['First name'] = 'Johann'
        self.default_dict['Last name'] = 'Gambolputty'
        self.test_object.configure({'action': 'slice',
                                    'start': 6,
                                    'end': None,
                                    'source_field': 'Last name',
                                    'target_field': 'Shorter last name'})
        for event in self.test_object.handleEvent(self.default_dict):
            print('%s' % event)
            self.assertTrue('Shorter last name' in event and event['Shorter last name'] == 'putty')

    def testReplaceStatic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.test_object.configure({'action': 'replace',
                                    'source_field': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': 'English'})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertEqual(event['replaceme'], 'The English Inquisition')

    def testReplaceDynamic(self):
        self.default_dict['replaceme'] = 'The Spanish Inquisition'
        self.default_dict['withme'] = 'English'
        self.test_object.configure({'action': 'replace',
                                    'source_field': 'replaceme',
                                    'regex': 'Sp.*?sh',
                                    'with': '$(withme)'})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertEqual(event['replaceme'], 'The English Inquisition')

    def testMap(self):
        self.default_dict['http_status'] = 100
        self.test_object.configure({'action': 'map',
                                    'source_field': 'http_status',
                                    'map': {100: 'Continue',
                                            200: 'OK'}
                                  })
        for event in self.test_object.handleEvent(self.default_dict):
            self.assert_('http_status_mapped' in event)
            self.assertEqual(event['http_status_mapped'], 'Continue')

    def testMapWithUnmappableFields(self):
        self.default_dict['http_status'] = 300
        self.test_object.configure({'action': 'map',
                                    'keep_unmappable': True,
                                    'source_field': 'http_status',
                                    'map': {100: 'Continue',
                                            200: 'OK'}
                                  })
        for event in self.test_object.handleEvent(self.default_dict):
            self.assert_('http_status_mapped' in event)
            self.assertEqual(event['http_status_mapped'], 300)

    def testMapWithTargetField(self):
        self.default_dict['http_status'] = 200
        self.test_object.configure({'action': 'map',
                                    'source_field': 'http_status',
                                    'map': {100: 'Continue',
                                            200: 'OK'},
                                    'target_field': 'http_status'
                                  })
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertEqual(event['http_status'], 'OK')

    def testKeep(self):
        self.default_dict['keep-this'] = 'The Spanish Inquisition'
        self.default_dict['keep-that'] = 'My hovercraft is full of eels!'
        self.default_dict['drop-this'] = 'English'
        self.test_object.configure({'action': 'keep',
                                    'source_fields': ['keep-this','keep-that']})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertTrue('keep-this' in event and 'keep-that' in event and 'drop-this' not in event)

    def testCastToInteger(self):
        self.default_dict['castable'] = '3'
        self.default_dict['non-castable'] = 'Three shall be the number thou shalt count, and the number of the counting shall be three.'
        self.test_object.configure({'action': 'cast_to_int',
                                    'source_fields': ['castable','non-castable', 'not-existing']})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertTrue('castable' in event and event['castable'] == 3)
            self.assertTrue('non-castable' in event and event['non-castable'] == 0)

    def testCastToFloat(self):
        self.default_dict['castable'] = '3.0'
        self.default_dict['non-castable'] = 'Three shall be the number thou shalt count, and the number of the counting shall be three.'
        self.test_object.configure({'action': 'cast_to_float',
                                    'source_fields': ['castable','non-castable', 'not-existing']})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertTrue('castable' in event and event['castable'] == 3.0)
            self.assertTrue('non-castable' in event and event['non-castable'] == 0)

    def testCastToString(self):
        self.default_dict['castable'] = 3.1415
        self.test_object.configure({'action': 'cast_to_str',
                                    'source_fields': ['castable', 'not-existing']})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertTrue('castable' in event and event['castable'] == "3.1415")

    def testCastToBoolean(self):
        self.default_dict['castable'] = 'True'
        self.test_object.configure({'action': 'cast_to_bool',
                                    'source_fields': ['castable', 'not-existing']})
        for event in self.test_object.handleEvent(self.default_dict):
            self.assertTrue('castable' in event and event['castable'] == True)

    def testReplaceFieldValueWithMd5Hash(self):
        self.test_object.configure({'action': 'hash',
                                    'source_fields': ['hash_me']})
        expected = DictUtils.getDefaultEventDict({'lumbermill': {'event_id': 1}, 'hash_me': 'bb649c83dd1ea5c9d9dec9a18df0ffe9'})
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({'lumbermill': {'event_id': 1}, 'hash_me': 'Nobody inspects the spammish repetition'})):
            self.assertEqual(event, expected)

    def testMd5Hash(self):
        self.test_object.configure({'action': 'hash',
                                    'source_fields': ['hash_me'],
                                    'target_fields': ['hash_me_hashed']})
        expected = DictUtils.getDefaultEventDict({'lumbermill': {'event_id': 1}, 'hash_me': 'Nobody inspects the spammish repetition', 'hash_me_hashed': 'bb649c83dd1ea5c9d9dec9a18df0ffe9'})
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({'lumbermill': {'event_id': 1}, 'hash_me': 'Nobody inspects the spammish repetition'})):
            self.assertEqual(event, expected)

    def testSha1Hash(self):
        self.test_object.configure({'action': 'hash',
                                    'algorithm': 'sha1',
                                    'source_fields': ['hash_me'],
                                    'target_fields': ['hash_me_hashed']})
        expected = DictUtils.getDefaultEventDict({'lumbermill': {'id': 1}, 'hash_me': 'Nobody inspects the spammish repetition', 'hash_me_hashed': '531b07a0f5b66477a21742d2827176264f4bbfe2'})
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({'lumbermill': {'id': 1}, 'hash_me': 'Nobody inspects the spammish repetition'})):
            self.assertEqual(event, expected)

    def testRenameRegex(self):
        self.test_object.configure({'action': 'rename_regex',
                                    'regex': '(Gam[Bb]olputty)\s+(Johann)-(.*)',
                                    'replace': '\\2 \\1 \\3'})
        data = DictUtils.getDefaultEventDict({'Gambolputty Johann-de von': 1,
                                              'Gambolputty Johann-de von Ausfern': 2,
                                              'Gambolputty Johann-de von Ausfern Schlingern Schlendern': 3})
        for event in self.test_object.handleEvent(data):
            self.assertIsNotNone(event)
            self.assertEqual(event['Johann Gambolputty de von'], 1)
            self.assertEqual(event['Johann Gambolputty de von Ausfern'], 2)
            self.assertEqual(event['Johann Gambolputty de von Ausfern Schlingern Schlendern'], 3)
        self.assertIsNotNone(event)

    def testRenameReplace(self):
        self.test_object.configure({'action': 'rename_replace',
                                    'old': 'Hannes',
                                    'new': 'Johann'})
        data = DictUtils.getDefaultEventDict({'Gambolputty Hannes de von': 1,
                                              'Gambolputty Hannes de von Ausfern': 2,
                                              'Gambolputty Hannes de von Ausfern Schlingern Schlendern': 3,})
        for event in self.test_object.handleEvent(data):
            self.assertIsNotNone(event)
            self.assertEqual(event['Gambolputty Johann de von'], 1)
            self.assertEqual(event['Gambolputty Johann de von Ausfern'], 2)
            self.assertEqual(event['Gambolputty Johann de von Ausfern Schlingern Schlendern'], 3)
        self.assertIsNotNone(event)

    def testKeyValue(self):
        self.test_object.configure({'action': 'key_value',
                                    'kv_separator': '-',
                                    'line_separator': '/',
                                    'source_field': 'url'})
        data = DictUtils.getDefaultEventDict({'lumbermill': {'event_id': 1}, 'url': 'Johann-Gambolputty/Schlingern-Schlendern/nobody-/spammish-repetition/'})
        for event in self.test_object.handleEvent(data):
            self.assertIsNotNone(event)
            self.assertEqual(event['Johann'], 'Gambolputty')
            self.assertEqual(event['Schlingern'], 'Schlendern')
            self.assertEqual(event['nobody'], '')
            self.assertEqual(event['spammish'], 'repetition')
        self.assertIsNotNone(event)

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