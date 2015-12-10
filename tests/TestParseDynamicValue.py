import unittest

import lumbermill.Utils as Utils


class TestParseDynaimcValue(unittest.TestCase):

    def testParseDynamicValues(self):
        self.assertTrue(Utils.parseDynamicValue('Default type to string: $(bytes_send)')['value'] == 'Default type to string: %(bytes_send)s')
        self.assertTrue(Utils.parseDynamicValue('String: $(lumbermill.event_id)s')['value'] == 'String: %(lumbermill.event_id)s')
        self.assertTrue(Utils.parseDynamicValue('Integer: $(lumbermill.list.0)d')['value'] == 'Integer: %(lumbermill.list.0)d')
        self.assertTrue(Utils.parseDynamicValue('Float: $(lumbermill.list.2.hovercraft)9.2f')['value'] == 'Float: %(lumbermill.list.2.hovercraft)9.2f')