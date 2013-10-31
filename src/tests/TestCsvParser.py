import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import re
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
        data = Utils.getDefaultDataDict({'csv-data': """It's;just;a;flesh;wound."""})
        result = self.test_object.handleData(data)
        self.assertTrue('brain' in result and result['brain'] == "just" )

    def testDelimiter(self):
        config = {'source_field': 'csv-data',
                  'escapechar': '\\',
                  'skipinitialspace': True,
                  'quotechar': '"',
                  'delimiter': '#',
                  'fieldnames': ["gumby", "brain", "specialist"] }
        self.test_object.configure(config)
        data = Utils.getDefaultDataDict({'csv-data': """It's#just#a#flesh#wound."""})
        result = self.test_object.handleData(data)
        print result
        self.assertTrue('brain' in result and result['brain'] == "just" )

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()