import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.parser import CsvParser


class TestCsvParser(ModuleBaseTestCase):

    def setUp(self):
        super(TestCsvParser, self).setUp(CsvParser.CsvParser(mock.Mock()))

    def testSimpleCsv(self):
        config = {'source_field': 'csv-data',
                  'escapechar': '\\',
                  'skipinitialspace': True,
                  'quotechar': '"',
                  'delimiter': ';',
                  'fieldnames': ["gumby", "brain", "specialist"] }
        self.test_object.configure(config)
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'csv-data': """It's;just;a;flesh;wound."""})
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
        data = DictUtils.getDefaultEventDict({'csv-data': """It's#just#a#flesh#wound."""})
        for event in self.test_object.handleEvent(data):
            self.assertTrue('brain' in event and event['brain'] == "just" )