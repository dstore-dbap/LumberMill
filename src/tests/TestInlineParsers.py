import pprint
import extendSysPath
import ModuleBaseTestCase
import sys
import time
import socket
import msgpack
import json
import TcpServer


class TestInlineParsers(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestInlineParsers, self).setUp(TcpServerTornado.TcpServerTornado(gp=ModuleBaseTestCase.MockGambolPutty()))
        self.test_object.configure({})
        self.checkConfiguration()

    def __testInlineMsgPackParser(self):
        inline_parser = self.test_object.gp.initModule('MsgPackParser')
        inline_parser.configure({'mode': 'stream'})
        self.test_object.addParser(inline_parser)
        self.test_object.start()
        self.startTornadoEventLoop()
        # Give server process time to startup.
        time.sleep(.1)
        orig_event = {'spam': 'spam' * 1}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(('localhost', self.test_object.getConfigurationValue('port')))
            connection_succeeded = True
        except:
            etype, evalue, etb = sys.exc_info()
            print "Could not connect to %s:%s. Exception: %s, Error: %s" % ('localhost', self.test_object.getConfigurationValue("port"), etype, evalue)
            connection_succeeded = False
        self.assertTrue(connection_succeeded)
        s.sendall(msgpack.packb(orig_event))
        s.close()
        received_event = False
        time.sleep(1)
        for received_event in self.receiver.getEvent():
            received_event.pop('gambolputty')
            self.assertDictEqual(received_event, orig_event)
        self.assertTrue(received_event != False)

    def __testInlineJsonParser(self):
        self.test_object.start()
        self.startTornadoEventLoop()
        # Give server process time to startup.
        time.sleep(.1)
        orig_event = {'spam': 'spam' * 2048}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(('localhost', self.test_object.getConfigurationValue('port')))
            connection_succeeded = True
        except:
            etype, evalue, etb = sys.exc_info()
            print "Could not connect to %s:%s. Exception: %s, Error: %s" % ('localhost', self.test_object.getConfigurationValue("port"), etype, evalue)
            connection_succeeded = False
        self.assertTrue(connection_succeeded)
        s.sendall(json.dumps(orig_event))
        s.close()
        received_event = False
        time.sleep(1)
        for received_event in self.receiver.getEvent():
            received_event.pop('gambolputty')
            self.assertDictEqual(received_event, orig_event)
        self.assertTrue(received_event != False)

    def __testChainedParsers(self):
        self.test_object.start()
        self.startTornadoEventLoop()
        # Give server process time to startup.
        time.sleep(.1)
        orig_event = {'spam': 'spam' * 1}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(('localhost', self.test_object.getConfigurationValue('port')))
            connection_succeeded = True
        except:
            etype, evalue, etb = sys.exc_info()
            print "Could not connect to %s:%s. Exception: %s, Error: %s" % ('localhost', self.test_object.getConfigurationValue("port"), etype, evalue)
            connection_succeeded = False
        self.assertTrue(connection_succeeded)
        s.sendall(msgpack.packb(json.dumps(orig_event)))
        s.close()
        received_event = False
        time.sleep(600)
        for received_event in self.receiver.getEvent():
            pprint.pprint(received_event)
            #received_event.pop('gambolputty')
            #self.assertDictEqual(received_event, orig_event)
        #self.assertTrue(received_event != False)