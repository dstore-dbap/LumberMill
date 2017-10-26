import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.parser import DateTimeParser


class TestDateTimeParser(ModuleBaseTestCase):

    def setUp(self):
        super(DateTimeParser, self).setUp(DateTimeParser.DateTimeParser())

    def testDateTimeParser(self):
        config = {'source_field': 'date',
                  'source_date_pattern': '%d/%b/Y',
                  'dest_date_pattern': '%d-%b-Y'}
        self.test_object.configure(config)
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'date': '13/Sep/2017'})
        for event in self.test_object.handleEvent(data):
            print(event)
            #self.assertTrue(event['splitted'] == expected_result)
