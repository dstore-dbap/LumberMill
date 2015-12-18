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
                 'params':  { u'spanish': [u'inquisition']},
                 'user': '-'}
        self.event = DictUtils.getDefaultEventDict(event)

    def testMapToUnknown(self):
        event = {
            'data': '<142>Dec 18 10:56:53 dstore.dbap.de apache2: httpd[12581] ssl.dbap.de 172.16.1.207 96025 "GET /my.dbap.de/SID=sidfb7dd2719cdd221f620f039bdd821/bottom.phtml?OldCounter=0 HTTP/1.1" 200 865 - 3e25df1469238006dcf5f1907fa1e4 "-" "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0"',
            'lumbermill': {'pid': 24712, 'event_type': 'httpd_access_log',
                           'event_id': '9fceabf13b030633d024b3e6d1e69f9524712', 'source_module': 'Spam',
                           'received_from': False, 'received_by': 'vagrant-centos65.vagrantup.com'},
            'syslog_prival': '<142>', 'log_timestamp': 'Dec 18 10:56:53', 'host': 'dstore.dbap.de',
            'server_type': 'apache2', 'pid': '12581', 'virtual_host_name': 'ssl.dbap.de', 'remote_ip': '172.16.1.207',
            'request_time': '96025', 'http_method': 'GET',
            'uri': '/my.dbap.de/SID=sidfb7dd2719cdd221f620f039bdd821/bottom.phtml?OldCounter=0', 'http_status': '200',
            'bytes_sent': '865', 'cookie_sid': '-', 'cookie_unique_id': '3e25df1469238006dcf5f1907fa1e4',
            'referer': '-', 'user_agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0'}
        print(mapDynamicValue("if %(gambolputty.event_type)s != 'agora_access_log'", event))

    def testMapDynamicValues(self):
        self.assertTrue(mapDynamicValue('%(bytes_send)s', self.event) == "3395")
        self.assertTrue(mapDynamicValue('%(lumbermill.event_id)s', self.event) == "715bd321b1016a442bf046682722c78e")
        self.assertTrue(mapDynamicValue('%(lumbermill.list.0)s', self.event) == "10")
        self.assertTrue(mapDynamicValue('%(lumbermill.list.2.hovercraft)s', self.event) == "eels")
        self.assertTrue(mapDynamicValue('%(params.spanish)s', self.event) == "[u'inquisition']")

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