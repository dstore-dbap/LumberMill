import extendSysPath
import ModuleBaseTestCase
import mock
import Utils
import RegexParser


class TestRegexParser(ModuleBaseTestCase.ModuleBaseTestCase):

    raw_data= '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/ HTTP/1.0" 200 3395'

    def setUp(self):
        super(TestRegexParser, self).setUp(RegexParser.RegexParser(gp=mock.Mock()))

    def testHandleEvent(self):
        self.test_object.configure({'source_field': 'event',
                                    'field_extraction_patterns': [{'http_access_log': '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<identd>\w+|-)\s+(?P<user>\w+|-)\s+\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s+\"(?P<url>.*)\"\s+(?P<http_status>\d+)\s+(?P<bytes_send>\d+)'}]})
        self.checkConfiguration()
        event = Utils.getDefaultEventDict({'event': self.raw_data})
        for event in self.test_object.handleEvent(event):
            self.assert_('bytes_send' in event and event['bytes_send'] == '3395')

    def tearDown(self):
        pass
