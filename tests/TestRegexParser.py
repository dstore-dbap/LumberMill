import ModuleBaseTestCase
import mock

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.parser import RegexParser


class TestRegexParser(ModuleBaseTestCase.ModuleBaseTestCase):

    raw_data = '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/ HTTP/1.0" 200 3395'

    multiline_raw_data = """Who shall declare this good, that ill
When good and ill so intertwine
But to fulfil the vast design of an omniscient will.
When seeming again but turns to loss
When earthly treasure proves but dross
And what seems lost but turns again
To high eternal gain."""

    def setUp(self):
        super(TestRegexParser, self).setUp(RegexParser.RegexParser(mock.Mock()))

    def testDefaultValues(self):
        self.test_object.configure({'field_extraction_patterns': [{'http_access_log': '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<identd>\w+|-)\s+(?P<user>\w+|-)\s+\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s+\"(?P<url>.*)\"\s+(?P<http_status>\d+)\s+(?P<bytes_send>\d+)'}]})
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'data': self.raw_data})
        event = None
        for event in self.test_object.handleEvent(data):
            self.assert_('bytes_send' in event and event['bytes_send'] == '3395')
        self.assertIsNotNone(event)

    def testMultilineWithoutRegexOptions(self):
        self.test_object.configure({'source_field': 'data',
                                    'field_extraction_patterns': [{'dame_irene': '(?P<poem>.*)'}]})
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'data': self.multiline_raw_data})
        event = None
        for event in self.test_object.handleEvent(data):
            self.assertEquals(self.multiline_raw_data.split('\n')[0], event['poem'])
            self.assertEquals(event['lumbermill.event_type'], 'dame_irene')
        self.assertIsNotNone(event)

    def testMultilineWithRegexOptions(self):
        self.test_object.configure({'source_field': 'data',
                                    'field_extraction_patterns': [{'dame_irene': ['(?P<poem>.*)', 're.MULTILINE | re.DOTALL']}]})
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'data': self.multiline_raw_data})
        event = None
        for event in self.test_object.handleEvent(data):
            print(event)
            self.assertEquals(self.multiline_raw_data, event['poem'])
            self.assertEquals(event['lumbermill.event_type'], 'dame_irene')
        self.assertIsNotNone(event)

    def testFindAllRegexOption(self):
        self.test_object.configure({'source_field': 'data',
                                    'field_extraction_patterns': [{'dame_irene': ['(?P<date>When)', 're.MULTILINE | re.DOTALL', 'findall']}]})
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'data': self.multiline_raw_data})
        event = None
        for event in self.test_object.handleEvent(data):
            self.assertEquals(event['lumbermill.event_type'], 'dame_irene')
            self.assertListEqual(event['date'], ['When', 'When', 'When'])
        self.assertIsNotNone(event)

    def testLogstashPattern(self):
        logstash_regex_pattern = '(?P<virtual_host_name>%{HOST}) (?P<remote_ip>%{IP})'
        parsed_regex_pattern = self.test_object.replaceLogstashPatterns(logstash_regex_pattern)
        print(parsed_regex_pattern)

    def tearDown(self):
        pass
