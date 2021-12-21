import unittest

from lumbermill.utils.DynamicValues import parseDynamicValue

class TestParseDynaimcValue(unittest.TestCase):

    def testParseDynamicValues(self):
        self.assertTrue(parseDynamicValue('default', 'Default type to string: $(bytes_send)')['value'] == 'Default type to string: %(bytes_send)s')
        self.assertTrue(parseDynamicValue('default', 'String: $(lumbermill.event_id)s')['value'] == 'String: %(lumbermill.event_id)s')
        self.assertTrue(parseDynamicValue('default', 'Integer: $(lumbermill.list.0)d')['value'] == 'Integer: %(lumbermill.list.0)d')
        self.assertTrue(parseDynamicValue('default', 'Float: $(lumbermill.list.2.hovercraft)9.2f')['value'] == 'Float: %(lumbermill.list.2.hovercraft)9.2f')