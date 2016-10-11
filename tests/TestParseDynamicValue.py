import unittest

from lumbermill.utils.DynamicValues import parseDynamicValue

class TestParseDynaimcValue(unittest.TestCase):

    def testParseDynamicValues(self):
        self.assertTrue(parseDynamicValue('Default type to string: $(bytes_send)')['value'] == 'Default type to string: %(bytes_send)s')
        self.assertTrue(parseDynamicValue('String: $(lumbermill.event_id)s')['value'] == 'String: %(lumbermill.event_id)s')
        self.assertTrue(parseDynamicValue('Integer: $(lumbermill.list.0)d')['value'] == 'Integer: %(lumbermill.list.0)d')
        self.assertTrue(parseDynamicValue('Float: $(lumbermill.list.2.hovercraft)9.2f')['value'] == 'Float: %(lumbermill.list.2.hovercraft)9.2f')