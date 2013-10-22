import extendSysPath
import unittest
import ModuleBaseTestCase
import mock
import Queue
import Utils
import RegexParser

class TestRegexParser(ModuleBaseTestCase.ModuleBaseTestCase):

    raw_data= '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/ HTTP/1.0" 200 3395'

    def setUp(self):
        super(TestRegexParser, self).setUp(RegexParser.RegexParser(gp=mock.Mock()))

    def testHandleData(self):
        self.test_object.configure({'source-fields': 'data',
                                    'field-extraction-patterns': {'http_access_log': '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<identd>\w+|-)\s+(?P<user>\w+|-)\s+\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s+\"(?P<url>.*)\"\s+(?P<http_status>\d+)\s+(?P<bytes_send>\d+)'}})
        data = Utils.getDefaultDataDict({'data': self.raw_data})
        result = self.test_object.handleData(data)
        self.assert_('bytes_send' in result and result['bytes_send'] == '3395')

    def testQueueCommunication(self):
        self.test_object.configure({'field-extraction-patterns': {'http_access_log': '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<identd>\w+|-)\s+(?P<user>\w+|-)\s+\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s+\"(?P<url>.*)\"\s+(?P<http_status>\d+)\s+(?P<bytes_send>\d+)'}})
        self.test_object.start()
        self.input_queue.put(Utils.getDefaultDataDict({}))
        queue_emtpy = False
        try:
            self.output_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy != True)

    def testQueueCommunication(self):
        config = {'field-extraction-patterns': {'http_access_log': '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<identd>\w+|-)\s+(?P<user>\w+|-)\s+\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s+\"(?P<url>.*)\"\s+(?P<http_status>\d+)\s+(?P<bytes_send>\d+)'}}
        super(TestRegexParser, self).testQueueCommunication(config)

    def testOutputQueueFilter(self):
        config = {'field-extraction-patterns': {'http_access_log': '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<identd>\w+|-)\s+(?P<user>\w+|-)\s+\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s+\"(?P<url>.*)\"\s+(?P<http_status>\d+)\s+(?P<bytes_send>\d+)'}}
        super(TestRegexParser, self).testOutputQueueFilter(config)

    def testInvertedOutputQueueFilter(self):
        config = {'field-extraction-patterns': {'http_access_log': '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<identd>\w+|-)\s+(?P<user>\w+|-)\s+\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s+\"(?P<url>.*)\"\s+(?P<http_status>\d+)\s+(?P<bytes_send>\d+)'}}
        super(TestRegexParser, self).testInvertedOutputQueueFilter(config)

    def testWorksOnCopy(self):
        config = {'field-extraction-patterns': {'http_access_log': '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<identd>\w+|-)\s+(?P<user>\w+|-)\s+\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s+\"(?P<url>.*)\"\s+(?P<http_status>\d+)\s+(?P<bytes_send>\d+)'}}
        super(TestRegexParser, self).testWorksOnCopy(config)

    def testWorksOnOriginal(self):
        config = {'field-extraction-patterns': {'http_access_log': '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<identd>\w+|-)\s+(?P<user>\w+|-)\s+\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s+\"(?P<url>.*)\"\s+(?P<http_status>\d+)\s+(?P<bytes_send>\d+)'}}
        super(TestRegexParser, self).testWorksOnOriginal(config)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()