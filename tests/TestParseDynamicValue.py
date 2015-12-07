import extendSysPath
import unittest2
import Utils

class TestParseDynaimcValue(unittest2.TestCase):

    def testParseDynamicValues(self):
        self.assertTrue(Utils.parseDynamicValue('Default type to string: $(bytes_send)')['value'] == 'Default type to string: %(bytes_send)s')
        self.assertTrue(Utils.parseDynamicValue('String: $(gambolputty.event_id)s')['value'] == 'String: %(gambolputty.event_id)s')
        self.assertTrue(Utils.parseDynamicValue('Integer: $(gambolputty.list.0)d')['value'] == 'Integer: %(gambolputty.list.0)d')
        self.assertTrue(Utils.parseDynamicValue('Float: $(gambolputty.list.2.hovercraft)9.2f')['value'] == 'Float: %(gambolputty.list.2.hovercraft)9.2f')