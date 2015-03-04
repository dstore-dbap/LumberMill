import extendSysPath
import ModuleBaseTestCase
import sys
import time
import mock
import socket
import msgpack
import TcpServer
import MsgPackParser

class TestMsgPackParser(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestMsgPackParser, self).setUp(MsgPackParser.MsgPackParser(gp=mock.Mock()))
        self.tcp_server = TcpServer.TcpServer(gp=mock.Mock())
        self.tcp_server.addReceiver("MsgPackParser", self.test_object)

    def testLineMode(self):
        self.tcp_server.configure({'mode': 'line'})
        self.tcp_server.initAfterFork()
        self.startTornadoEventLoop()
        self.test_object.configure({'mode': 'line'})
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
        s.sendall(msgpack.packb(orig_event)+ "\n")
        s.close()
        received_event = False
        time.sleep(.1)
        # Needs to be done here, otherwise travis-ci will throw an error when another module calls startTornadoEventLoop().
        self.stopTornadoEventLoop()
        for received_event in self.receiver.getEvent():
            received_event.pop('gambolputty')
            self.assertDictEqual(received_event, orig_event)
        self.assertTrue(received_event != False)

    def testStreamMode(self):
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
        # Needs to be done here, otherwise travis-ci will throw an error when another module calls startTornadoEventLoop().
        self.stopTornadoEventLoop()
        for received_event in self.receiver.getEvent():
            received_event.pop('gambolputty')
            self.assertDictEqual(received_event, orig_event)
        self.assertTrue(received_event != False)

    def tearDown(self):
        self.tcp_server.shutDown()
        ModuleBaseTestCase.ModuleBaseTestCase.tearDown(self)