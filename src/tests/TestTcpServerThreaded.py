import extendSysPath
import ModuleBaseTestCase
import Utils
import sys
import time
import mock
import socket
import ssl
import TcpServerThreaded

class TestTcpServerThreaded(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestTcpServerThreaded, self).setUp(TcpServerThreaded.TcpServerThreaded(gp=mock.Mock()))

    def testTcpConnection(self):
        self.test_object.configure({})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.run()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(.2)
            s.connect((self.test_object.getConfigurationValue('interface'), self.test_object.getConfigurationValue('port')))
            s.sendall("Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever.")
            s.close()
            connection_succeeded = True
        except:
            etype, evalue, etb = sys.exc_info()
            print "Could not connect to %s:%s. Exception: %s, Error: %s" % ( self.test_object.getConfigurationValue("interface"),
                                                                            self.test_object.getConfigurationValue("port"), etype, evalue)
            connection_succeeded = False
        self.assertTrue(connection_succeeded)
        time.sleep(.1)
        expected_ret_val = Utils.getDefaultEventDict({'received_from': '127.0.0.1', 'data': "Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever."})
        expected_ret_val.pop('gambolputty')
        event = False
        for event in self.receiver.getEvent():
            event.pop('gambolputty')
            self.assertDictEqual(event, expected_ret_val)
        self.assertTrue(event != False)

    def testTlsTcpConnection(self):
        self.test_object.configure({'tls': True,
                                    'key': '../../exampleData/gambolputty_ca.key',
                                    'cert': '../../exampleData/gambolputty_ca.crt',
                                    'timeout': 1})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.run()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(.2)
            s = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv23)
            s.connect((self.test_object.getConfigurationValue('interface'), self.test_object.getConfigurationValue('port')))
            s.sendall("Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever.")
            s.close()
            connection_succeeded = True
        except:
            etype, evalue, etb = sys.exc_info()
            print "Could not connect to %s:%s. Exception: %s, Error: %s" % ( self.test_object.getConfigurationValue("interface"),
                                                                            self.test_object.getConfigurationValue("port"), etype, evalue)
            connection_succeeded = False
        self.assertTrue(connection_succeeded)
        self.test_object.gp.shutDown()
        # Give server some time to shut socket down.
        time.sleep(.1)
        expected_ret_val = Utils.getDefaultEventDict({'received_from': '127.0.0.1', 'data': "Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever."})
        expected_ret_val.pop('gambolputty')
        event = False
        for event in self.receiver.getEvent():
            event.pop('gambolputty')
            self.assertDictEqual(event, expected_ret_val)
        self.assertTrue(event != False)

    def tearDown(self):
        self.test_object.shutDown(silent=True)
        time.sleep(1)