import pprint
import unittest
import lumbermill.utils.DictUtils as DictUtils


class TestKeyDotNotationDict(unittest.TestCase):

    def setUp(self):
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
                 'identd': '-',
                 'remote_ip': '192.168.2.20',
                 'url': 'GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0',
                 'fields': ['nobody', 'expects', 'the'],
                 'params':  { u'spanish': [u'inquisition']},
                 'empty': {},
                 'user': '-'}
        self.event = DictUtils.getDefaultEventDict(event)

    def testDotAccessToDict(self):
        self.assertTrue(self.event['bytes_send'] == 3395)
        self.assertTrue(self.event['lumbermill.event_id'] == "715bd321b1016a442bf046682722c78e")
        self.assertTrue(self.event['params.spanish'] == [u'inquisition'])

    def testDotAccessToList(self):
        self.assertTrue(self.event['lumbermill.list.0'] == 10)
        self.assertTrue(self.event['lumbermill.list.2.hovercraft'] == 'eels')

    def testDotAccessToDictWithDefault(self):
        self.assertTrue(self.event.get('lumbermill.event_id', 'default value') == "715bd321b1016a442bf046682722c78e")
        self.assertTrue(self.event.get('lumbermill.missing_key', 'default value') == "default value")
        self.assertTrue(self.event.get('lumbermill.list.2.hovercraft', 'default value') == 'eels')
        self.assertTrue(self.event.get('lumbermill.list.3.hovercraft', 'default value') == 'default value')

    def testSetViaDotAccess(self):
        self.event['params.nobody'] = 'expects'
        self.event['empty.nobody'] = 'expects'
        self.assertRaises(IndexError, self.event.get, 'nobody')
        self.assertTrue(self.event.get('params.nobody') == 'expects')
        self.assertTrue(self.event.get('empty.nobody') == 'expects')
        self.assertTrue(self.event.get('params.spanish.0') == 'inquisition')