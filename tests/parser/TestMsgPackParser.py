import sys
import time
import mock
import socket
import msgpack
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.input import TcpServer
from lumbermill.parser import MsgPackParser


class TestMsgPackParser(ModuleBaseTestCase):

    def setUp(self):
        super(TestMsgPackParser, self).setUp(MsgPackParser.MsgPackParser(mock.Mock()))
        self.tcp_server = TcpServer.TcpServer(mock.Mock())
        self.tcp_server.addReceiver("MsgPackParser", self.test_object)

    def testEncodeLineMode(self):
        self.test_object.configure({'action': 'encode',
                                    'mode': 'line',
                                    'source_fields': 'data',
                                    'target_field': 'data'})
        self.checkConfiguration()
        data = {'data': {'spam': 'spam'}}
        msg_packed_data = msgpack.packb(data)
        dict = DictUtils.getDefaultEventDict(data)
        event = None
        for event in self.test_object.handleEvent(dict):
            self.assertEquals(event['data'], msg_packed_data)
        self.assertIsNotNone(event)

    def testEncodeLineModeWithDropOriginal(self):
        self.test_object.configure({'action': 'encode',
                                    'mode': 'line',
                                    'source_fields': 'data',
                                    'target_field': 'data_packed',
                                    'keep_original': False})
        self.checkConfiguration()
        data = {'data': {'spam': 'spam'}}
        msg_packed_data = msgpack.packb(data)
        dict = DictUtils.getDefaultEventDict(data)
        event = None
        for event in self.test_object.handleEvent(dict):
            self.assertEquals(event['data_packed'], msg_packed_data)
            self.assertNotIn('data', event)
        self.assertIsNotNone(event)

    def testDecodeLineMode(self):
        self.test_object.configure({'mode': 'line'})
        self.checkConfiguration()
        data = {'spam': 'spam' * 16384}
        msg_packed_data = msgpack.packb(data)
        dict = DictUtils.getDefaultEventDict({'data': msg_packed_data})
        event = None
        for event in self.test_object.handleEvent(dict):
            self.assertEquals(event['spam'], data['spam'])
        self.assertIsNotNone(event)

    def testDecodeStreamMode(self):
        self.tcp_server.configure({'mode': 'stream'})
        self.tcp_server.initAfterFork()
        self.startTornadoEventLoop()
        self.test_object.configure({'mode': 'stream'})
        self.checkConfiguration()
        orig_event = {'spam': 'spam' * 16384}
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
        s.sendall(msgpack.packb(orig_event))
        s.close()
        received_event = False
        time.sleep(.1)
        for received_event in self.receiver.getEvent():
            received_event.pop('lumbermill')
            self.assertDictEqual(received_event, orig_event)
        self.assertTrue(received_event != False)

    def tearDown(self):
        self.tcp_server.shutDown()
        ModuleBaseTestCase.tearDown(self)