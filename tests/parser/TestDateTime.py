import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.parser import DateTime


class TestDateTime(ModuleBaseTestCase):

    def setUp(self):
        super(TestDateTime, self).setUp(DateTime.DateTime(mock.Mock()))

    def testDateTime(self):
        config = {'source_field': 'date',
                  'source_date_pattern': '%d/%b/%Y',
                  'target_date_pattern': '%d-%b-%Y'}
        self.test_object.configure(config)
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'date': '13/Sep/2017'})
        for event in self.test_object.handleEvent(data):
            self.assertTrue(event['date'] == "13-Sep-2017")
