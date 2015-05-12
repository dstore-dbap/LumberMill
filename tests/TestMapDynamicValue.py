import extendSysPath
import logging
import unittest2
import Utils

class TestMapDynaimcValue(unittest2.TestCase):

    def setUp(self):
        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        event = {'bytes_send': 3395,
                 'data': '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0" 200 3395\n',
                 'datetime': '28/Jul/2006:10:27:10 -0300',
                 'gambolputty': {
                                'event_id': '715bd321b1016a442bf046682722c78e',
                                'event_type': 'httpd_access_log',
                                'received_from': '127.0.0.1',
                                'source_module': 'StdInHandler',
                                'list': [10, 20, {'hovercraft': 'eels'}]
                  },
                 'http_status': 200,
                 'identd': '-',
                 'remote_ip': '192.168.2.20',
                 'url': 'GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0',
                 'fields': ['nobody', 'expects', 'the'],
                 'params':  { u'spanish': [u'inquisition']},
                 'user': '-'}
        self.event = Utils.getDefaultEventDict(event)

    def testMapDynamicValues(self):
        self.assertTrue(Utils.mapDynamicValue('%(bytes_send)s', self.event) == "3395")
        self.assertTrue(Utils.mapDynamicValue('%(gambolputty.event_id)s', self.event) == "715bd321b1016a442bf046682722c78e")
        self.assertTrue(Utils.mapDynamicValue('%(gambolputty.list.0)s', self.event) == "10")
        self.assertTrue(Utils.mapDynamicValue('%(gambolputty.list.2.hovercraft)s', self.event) == "eels")
        self.assertTrue(Utils.mapDynamicValue('%(params.spanish)s', self.event) == "[u'inquisition']")

    def testMapDynamicValueWithMissingKey(self):
        self.assertTrue(Utils.mapDynamicValue('%(missing_key)s', self.event) == '%(missing_key)s')