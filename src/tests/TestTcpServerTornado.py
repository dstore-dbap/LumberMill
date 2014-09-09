import extendSysPath
import ModuleBaseTestCase
import Utils
import sys
import time
import mock
import socket
import ssl
import TcpServerTornado

class TestTcpServerTornado(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestTcpServerTornado, self).setUp(TcpServerTornado.TcpServerTornado(gp=mock.Mock()))

    def testTcpConnection(self):
        self.test_object.configure({})
        self.checkConfiguration()
        self.test_object.start()
        self.startTornadoEventLoop()
        # Give server process time to startup.
        time.sleep(.1)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect(('localhost', self.test_object.getConfigurationValue('port')))
            s.sendall("Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever.\n")
            s.close()
            connection_succeeded = True
        except:
            etype, evalue, etb = sys.exc_info()
            print "Could not connect to %s:%s. Exception: %s, Error: %s" % ( 'localhost', self.test_object.getConfigurationValue("port"), etype, evalue)
            connection_succeeded = False
        self.assertTrue(connection_succeeded)
        expected_ret_val = Utils.getDefaultEventDict({'data': "Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever."})
        expected_ret_val.pop('gambolputty')
        event = False
        time.sleep(.1)
        for event in self.receiver.getEvent():
            event.pop('gambolputty')
            self.assertDictEqual(event, expected_ret_val)
        self.assertTrue(event != False)

    def testTlsTcpConnection(self):
        self.test_object.configure({'port': 5252,
                                    'tls': True,
                                    'key': '../../exampleData/gambolputty_ca.key',
                                    'cert': '../../exampleData/gambolputty_ca.crt',
                                    'timeout': 1})
        self.checkConfiguration()
        self.test_object.start()
        self.startTornadoEventLoop()
        # Give server process time to startup.
        time.sleep(1)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv23)
            s.connect((self.test_object.getConfigurationValue('interface'), self.test_object.getConfigurationValue('port')))
            s.sendall("Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever.\n")
            s.close()
            connection_succeeded = True
        except:
            etype, evalue, etb = sys.exc_info()
            print "Could not connect to %s:%s. Exception: %s, Error: %s" % ( self.test_object.getConfigurationValue("interface"),
                                                                            self.test_object.getConfigurationValue("port"), etype, evalue)
            connection_succeeded = False
        self.assertTrue(connection_succeeded)
        expected_ret_val =  Utils.getDefaultEventDict({'data': "Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever."})
        expected_ret_val.pop('gambolputty')
        event = False
        time.sleep(.1)
        for event in self.receiver.getEvent():
            event.pop('gambolputty')
            self.assertDictEqual(event, expected_ret_val)
        self.assertTrue(event != False)

    def tearDown(self):
        self.test_object.shutDown(silent=True)
        # Give server process some time to shut down.
        time.sleep(1)