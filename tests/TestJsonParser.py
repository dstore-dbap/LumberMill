import ModuleBaseTestCase
import mock
import socket
import json
import sys
import time

import lumbermill.Utils as Utils
from lumbermill.input import TcpServer
from lumbermill.parser import JsonParser


class TestJsonParser(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestJsonParser, self).setUp(JsonParser.JsonParser(mock.Mock()))
        self.tcp_server = TcpServer.TcpServer(mock.Mock())
        self.tcp_server.addReceiver("JsonParser", self.test_object)

    def testLineMode(self):
        self.tcp_server.configure({'mode': 'line'})
        self.tcp_server.initAfterFork()
        self.startTornadoEventLoop()
        self.test_object.configure({})
        self.checkConfiguration()
        orig_event = {'json_data': {'South African': 'Fast',
                                    'unladen': 'swallow'}}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(('localhost', self.tcp_server.getConfigurationValue('port')))
            connection_succeeded = True
        except:
            etype, evalue, etb = sys.exc_info()
            print "Could not connect to %s:%s. Exception: %s, Error: %s" % ('localhost', self.test_object.getConfigurationValue("port"), etype, evalue)
            connection_succeeded = False
        self.assertTrue(connection_succeeded)
        s.sendall(json.dumps(orig_event) + "\n")
        s.close()
        received_event = False
        time.sleep(.1)
        for received_event in self.receiver.getEvent():
            received_event.pop('lumbermill')
            self.assertDictEqual(received_event, orig_event)
        self.assertTrue(received_event is not False)

    def __testStreamMode(self):
        self.tcp_server.configure({'mode': 'stream'})
        self.tcp_server.initAfterFork()
        self.startTornadoEventLoop()
        self.test_object.configure({})
        self.checkConfiguration()
        orig_event = {'json_data': {'South African': 'Fast' * 8192,
                                    'unladen': 'swallow'}}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(('localhost', self.tcp_server.getConfigurationValue('port')))
            connection_succeeded = True
        except:
            etype, evalue, etb = sys.exc_info()
            print "Could not connect to %s:%s. Exception: %s, Error: %s" % ('localhost', self.test_object.getConfigurationValue("port"), etype, evalue)
            connection_succeeded = False
        self.assertTrue(connection_succeeded)
        s.sendall(json.dumps(orig_event))
        s.close()
        received_event = False
        time.sleep(.1)
        for received_event in self.receiver.getEvent():
            received_event.pop('lumbermill')
            self.assertDictEqual(received_event, orig_event)
        self.assertTrue(received_event is not False)

    def __testSimpleJson(self):
        self.test_object.configure({'source_fields': ['json_data']})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        data = Utils.getDefaultEventDict({'json_data': '{\'South African\': \'Fast\', \'unladen\': \'swallow\'}'})
        for event in self.test_object.handleEvent(data):
            self.assertTrue('South African' in event and event['South African'] == "Fast" )

    def tearDown(self):
        self.tcp_server.shutDown()
        ModuleBaseTestCase.ModuleBaseTestCase.tearDown(self)
        pass