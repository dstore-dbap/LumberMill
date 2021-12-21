import datetime
import logging
import unittest
import lumbermill.utils.DictUtils as DictUtils

from lumbermill.utils.DynamicValues import mapDynamicValue


class TestMapDynaimcValue(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        event = {'bytes_send': 3395,
                 'data': '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0" 200 3395\n',
                 'datetime': '28/Jul/2006:10:27:10 -0300',
                 'lumbermill': {
                                'event_id': '715bd321b1016a442bf046682722c78e',
                                'event_type': 'httpd_access_log',
                                'received_from': '127.0.0.1',
                                'source_module': 'StdIn',
                                'list': [10, 20, {'hovercraft': 'eels'}]
                  },
                 'http_status': 200,
                 'longitude': 7.626,
                 'latitude': 51.960,
                 'identd': '-',
                 'remote_ip': '192.168.2.20',
                 'url': 'GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0',
                 'fields': ['nobody', 'expects', 'the'],
                 'params': { u'spanish': [u'inquisition']},
                 'user': '-'}
        self.event = DictUtils.getDefaultEventDict(event)

    def testMapDynamicValues(self):
        self.assertTrue(mapDynamicValue('%(bytes_send)s', self.event) == "3395")
        self.assertTrue(mapDynamicValue('%(lumbermill.event_id)s', self.event) == "715bd321b1016a442bf046682722c78e")
        self.assertTrue(mapDynamicValue('%(lumbermill.list.0)s', self.event) == "10")
        self.assertTrue(mapDynamicValue('%(lumbermill.list.2.hovercraft)s', self.event) == "eels")
        self.assertTrue(mapDynamicValue('%(params.spanish)s', self.event) == "['inquisition']")

    def testMapDynamicValueWithMissingKey(self):
        self.assertTrue(mapDynamicValue('%(missing_key)s', self.event) == '%(missing_key)s')

    def testMapDynamicValueWithTimePattern(self):
        timestring = datetime.datetime.utcnow().strftime('%Y.%m.%d')
        self.assertTrue(mapDynamicValue('test-%Y.%m.%d-%(lumbermill.event_id)s', self.event, use_strftime=True) == 'test-%s-715bd321b1016a442bf046682722c78e' % timestring)

    def testMapDynamicValueWithValueFormat(self):
        self.assertTrue(mapDynamicValue('%(longitude)d', self.event) == '7')
        self.assertTrue(mapDynamicValue('%(longitude)+d', self.event) == '+7')
        self.assertTrue(mapDynamicValue('%(longitude)05.2f', self.event) == '07.63')
        self.assertTrue(mapDynamicValue('%(fields.1)10s', self.event) == '   expects')
        self.assertTrue(mapDynamicValue('%(fields.1)-10s', self.event) == 'expects   ')
        self.assertTrue(mapDynamicValue('%(fields.1).5s', self.event) == 'expec')
        self.assertTrue(mapDynamicValue('%(fields.1)-10.5s', self.event) == 'expec     ')

    def testMapDynamicValueWithDictType(self):
        # Make sure that mapDynamicValue will work on a copy of value when passing in a list or a dict.
        mapping_dict = {'event_id': '%(lumbermill.event_id)s'}
        mapped_values = mapDynamicValue(mapping_dict, self.event)
        self.assertEqual(mapped_values['event_id'], '715bd321b1016a442bf046682722c78e')
        self.assertEqual(mapping_dict, {'event_id': '%(lumbermill.event_id)s'})

    def testMapDynamicValueWithListType(self):
        # Make sure that mapDynamicValue will work on a copy of value when passing in a list or a dict.
        mapping_list = ['%(lumbermill.event_id)s']
        mapped_values = mapDynamicValue(mapping_list, self.event)
        self.assertEqual(mapped_values[0], '715bd321b1016a442bf046682722c78e')
        self.assertEqual(mapping_list, ['%(lumbermill.event_id)s'])

    def testMapDynamicValueWithNoneType(self):
        self.assertEqual(mapDynamicValue(None, self.event), None)