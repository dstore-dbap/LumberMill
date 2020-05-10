import sys
import time
import mock
import socket
import msgpack
import unittest

import lumbermill.utils.DictUtils as DictUtils
from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.input import Tcp
from lumbermill.parser import MsgPack
from tests.ServiceDiscovery import getFreeTcpPortoOnLocalhost


class TestMsgPack(ModuleBaseTestCase):

    def setUp(self):
        super(TestMsgPack, self).setUp(MsgPack.MsgPack(mock.Mock()))
        self.tcp_server = Tcp.Tcp(mock.Mock())
        self.tcp_server.addReceiver("MsgPack", self.test_object)

    def testEncodeLineMode(self):
        self.test_object.configure({'action': 'encode',
                                    'mode': 'line',
                                    'source_fields': 'data',
                                    'target_field': 'data'})
        self.checkConfiguration()
        data = {'data': {'spam': 'spam'}}
        msg_packed_data = msgpack.packb(data, encoding="utf-8")
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
        msg_packed_data = msgpack.packb(data, encoding="utf-8")
        dict = DictUtils.getDefaultEventDict(data)
        event = None
        for event in self.test_object.handleEvent(dict):
            self.assertEquals(event['data_packed'], msg_packed_data)
            self.assertNotIn('data', event)
        self.assertIsNotNone(event)

    def testDecodeLineMode(self):
        self.test_object.configure({'mode': 'line',
                                    'source_fields': 'spam',
                                    'target_field': 'spam_decoded'})
        self.checkConfiguration()
        data = {'spam': 'spam' * 8}
        msg_packed_data = msgpack.packb(data, encoding="utf-8")
        dict = DictUtils.getDefaultEventDict({'spam': msg_packed_data})
        event = None
        for event in self.test_object.handleEvent(dict):
            self.assertEquals(event['spam_decoded'], data)
        self.assertIsNotNone(event)

    def testDecodeStreamMode(self):
        raise unittest.SkipTest('Stream mode decoding is only for testing. Skipping unittest.')
        ipaddr, port = getFreeTcpPortoOnLocalhost()
        self.tcp_server.configure({'interface': ipaddr,
                                    'port': port,
                                    'mode': 'stream',})
        self.tcp_server.initAfterFork()
        self.startTornadoEventLoop()
        self.test_object.configure({'mode': 'stream',
                                    'source_fields': 'data',
                                    'target_field': 'spam_decoded'})
        self.checkConfiguration()
        orig_event = {'spam': 'spam' * 16384}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(('localhost', self.tcp_server.getConfigurationValue('port')))
            connection_succeeded = True
        except:
            etype, evalue, etb = sys.exc_info()
            print("Could not connect to %s:%s. Exception: %s, Error: %s" % ('localhost', self.test_object.getConfigurationValue("port"), etype, evalue))
            connection_succeeded = False
        self.assertTrue(connection_succeeded)
        s.sendall(msgpack.packb(orig_event, encoding="utf-8"))
        s.close()
        received_event = False
        time.sleep(.5)
        for received_event in self.receiver.getEvent():
            print("asdads")
            received_event.pop('lumbermill')
            self.assertDictEqual(received_event, orig_event)
        self.assertTrue(received_event)

    def tearDown(self):
        self.tcp_server.shutDown()
        ModuleBaseTestCase.tearDown(self)