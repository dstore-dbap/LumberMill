import extendSysPath
import ModuleBaseTestCase
import mock
import Utils
import CsvParser

class TestCsvParser(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestCsvParser, self).setUp(CsvParser.CsvParser(gp=mock.Mock()))

    def testSimpleCsv(self):
        config = {'source_field': 'csv-data',
                  'escapechar': '\\',
                  'skipinitialspace': True,
                  'quotechar': '"',
                  'delimiter': ';',
                  'fieldnames': ["gumby", "brain", "specialist"] }
        self.test_object.configure(config)
        self.checkConfiguration()
        data = Utils.getDefaultEventDict({'csv-data': """It's;just;a;flesh;wound."""})
        for event in self.test_object.handleEvent(data):
            self.assertTrue('brain' in event and event['brain'] == "just" )

    def testDelimiter(self):
        config = {'source_field': 'csv-data',
                  'escapechar': '\\',
                  'skipinitialspace': True,
                  'quotechar': '"',
                  'delimiter': '#',
                  'fieldnames': ["gumby", "brain", "specialist"] }
        self.test_object.configure(config)
        self.checkConfiguration()
        data = Utils.getDefaultEventDict({'csv-data': """It's#just#a#flesh#wound."""})
        for event in self.test_object.handleEvent(data):
            self.assertTrue('brain' in event and event['brain'] == "just" )

    def tearDown(self):
        pass