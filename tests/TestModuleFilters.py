import extendSysPath
import ModuleBaseTestCase
import mock
import Utils
import Math

class TestModuleFilters(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        event = {'bytes_send': 3395,
                 'data': '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0" 200 3395\n',
                 'datetime': '28/Jul/2006:10:27:10 -0300',
                 'gambolputty': {
                                'event_id': '715bd321b1016a442bf046682722c78e',
                                'event_type': 'httpd_access_log',
                                'received_from': '127.0.0.1',
                                'source_module': 'StdIn',
                                'list': [10, 20, {'hovercraft': 'eels'}]
                  },
                 'http_status': 200,
                 'cache_hits': 5,
                 'identd': '-',
                 'remote_ip': '192.168.2.20',
                 'url': 'GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0',
                 'fields': ['nobody', 'expects', 'the'],
                 'params':  { u'spanish': [u'inquisition']},
                 'user': '-'}
        self.event = Utils.getDefaultEventDict(event)
        super(TestModuleFilters, self).setUp(Math.Math(gp=mock.Mock()))

    def testInputFilterMatch(self):
        self.test_object.configure({'filter': 'if $(gambolputty.source_module) == "StdIn" and $(gambolputty.list.2.hovercraft) == "eels"',
                                    'target_field': 'test',
                                    'function': 'int($(cache_hits)) * 2'})
        self.checkConfiguration()
        self.test_object.receiveEvent(self.event)
        for event in self.receiver.getEvent():
            self.assertTrue(event['test'] == 10)

    def testInputFilterNoMatch(self):
        self.test_object.configure({'filter': 'if $(gambolputty.source_module) == "StdIn" and $(gambolputty.list.2.hovercraft) == "fish"',
                                    'target_field': 'test',
                                    'function': 'int($(cache_hits)) * 2'})
        self.checkConfiguration()
        self.test_object.receiveEvent(self.event)
        for event in self.receiver.getEvent():
            self.assertTrue('test' not in event)

    def testOutputFilterMatch(self):
        self.test_object.configure({'target_field': 'test',
                                    'function': 'int($(cache_hits)) * 2',
                                    'receivers': [{'MockReceiver': {
                                                      'filter': 'if $(gambolputty.source_module) == "StdIn"'}}]})
        self.checkConfiguration()
        self.test_object.receiveEvent(self.event)
        received_event = None
        for event in self.receiver.getEvent():
            received_event = event
        self.assertTrue(received_event != None)

    def testOutputFilterNoMatch(self):
        self.test_object.configure({'target_field': 'test',
                                    'function': 'int($(cache_hits)) * 2',
                                    'receivers': [{'MockReceiver': {
                                                      'filter': 'if $(gambolputty.source_module) != "StdIn"'}}]})
        self.checkConfiguration()
        self.test_object.receiveEvent(self.event)
        received_event = None
        for event in self.receiver.getEvent():
            received_event = event
        self.assertTrue(received_event == None)