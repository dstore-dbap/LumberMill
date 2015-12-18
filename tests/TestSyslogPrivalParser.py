import ModuleBaseTestCase
import mock

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.parser import SyslogPrivalParser


class TestSyslogPrivalParser(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestSyslogPrivalParser, self).setUp(SyslogPrivalParser.SyslogPrivalParser(mock.Mock()))

    def testNumericalSyslogPrivalFields(self):
        config = {'source_field': 'syslog_prival',
                  'map_values': False}
        self.test_object.configure(config)
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'syslog_prival': '13', 'data': 'This is an ex parrot!'})
        event = False
        for event in self.test_object.handleEvent(data):
            self.assertTrue('syslog_severity' in event and event['syslog_severity'] == 5 )
            self.assertTrue('syslog_facility' in event and event['syslog_facility'] == 1 )
        self.assertTrue(event != False)

    def testDefaultMappedSyslogPrivalFields(self):
        config = {'source_field': 'syslog_prival',
                  'map_values': True}
        self.test_object.configure(config)
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'syslog_prival': '13', 'data': 'This is an ex parrot!'})
        event = False
        for event in self.test_object.handleEvent(data):
            self.assertTrue('syslog_severity' in event and event['syslog_severity'] == "Notice" )
            self.assertTrue('syslog_facility' in event and event['syslog_facility'] == "user-level" )
        self.assertTrue(event != False)

    def testCustomMappedSyslogPrivalFields(self):
        config = {'source_field': 'syslog_prival',
                  'map_values': True,
                  'facility_mappings': {1: 'PetShopBolton'},
                  'severity_mappings': {5: 'DeadParrotException'}}
        self.test_object.configure(config)
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'syslog_prival': '13', 'data': 'This is an ex parrot!'})
        event = False
        for event in self.test_object.handleEvent(data):
            self.assertTrue('syslog_severity' in event and event['syslog_severity'] == "DeadParrotException" )
            self.assertTrue('syslog_facility' in event and event['syslog_facility'] == "PetShopBolton" )
        self.assertTrue(event != False)