import extendSysPath
import unittest2
import Utils

class TestKeyDotNotationDict(unittest2.TestCase):

    def setUp(self):
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

    def testKeyDotNotationDict(self):
        self.assertTrue(self.event['bytes_send'] == 3395)
        self.assertTrue(self.event['gambolputty.event_id'] == "715bd321b1016a442bf046682722c78e")
        self.assertTrue(self.event['gambolputty.list.0'] == 10)
        self.assertTrue(self.event['gambolputty.list.2.hovercraft'] == 'eels')
        self.assertTrue(self.event['params.spanish'] == [u'inquisition'])
