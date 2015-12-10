import datetime
import logging
import unittest

import lumbermill.Utils as Utils


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
                 'params':  { u'spanish': [u'inquisition']},
                 'user': '-'}
        self.event = Utils.getDefaultEventDict(event)

    def testMapDynamicValues(self):
        self.assertTrue(Utils.mapDynamicValue('%(bytes_send)s', self.event) == "3395")
        self.assertTrue(Utils.mapDynamicValue('%(lumbermill.event_id)s', self.event) == "715bd321b1016a442bf046682722c78e")
        self.assertTrue(Utils.mapDynamicValue('%(lumbermill.list.0)s', self.event) == "10")
        self.assertTrue(Utils.mapDynamicValue('%(lumbermill.list.2.hovercraft)s', self.event) == "eels")
        self.assertTrue(Utils.mapDynamicValue('%(params.spanish)s', self.event) == "[u'inquisition']")

    def testMapDynamicValueWithMissingKey(self):
        self.assertTrue(Utils.mapDynamicValue('%(missing_key)s', self.event) == '%(missing_key)s')

    def testMapDynamicValueWithTimePattern(self):
        timestring = datetime.datetime.utcnow().strftime('%Y.%m.%d')
        self.assertTrue(Utils.mapDynamicValue('test-%Y.%m.%d-%(lumbermill.event_id)s', self.event, use_strftime=True) == 'test-%s-715bd321b1016a442bf046682722c78e' % timestring)

    def testMapDynamicValueWithValueFormat(self):
        self.assertTrue(Utils.mapDynamicValue('%(longitude)d', self.event) == '7')
        self.assertTrue(Utils.mapDynamicValue('%(longitude)+d', self.event) == '+7')
        self.assertTrue(Utils.mapDynamicValue('%(longitude)05.2f', self.event) == '07.63')
        self.assertTrue(Utils.mapDynamicValue('%(fields.1)10s', self.event) == '   expects')
        self.assertTrue(Utils.mapDynamicValue('%(fields.1)-10s', self.event) == 'expects   ')
        self.assertTrue(Utils.mapDynamicValue('%(fields.1).5s', self.event) == 'expec')
        self.assertTrue(Utils.mapDynamicValue('%(fields.1)-10.5s', self.event) == 'expec     ')