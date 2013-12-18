import extendSysPath
import ModuleBaseTestCase
import Utils
import unittest2
import sys
import Queue
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
            s.settimeout(0.2)
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
        expected_ret_val = Utils.getDefaultEventDict({'received_from': '127.0.0.1', 'data': "Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever."})
        self.test_object.shutDown()
        for event in self.receiver.getEvent():
            self.assertEquals(event, expected_ret_val)

    def testATlsTcpConnection(self):
        self.test_object.configure({'tls': True,
                                    'key': '/Volumes/bputtmann/public_html/GambolPutty/src/exampleData/gambolputty_ca.key',
                                    'cert': '/Volumes/bputtmann/public_html/GambolPutty/src/exampleData/gambolputty_ca.crt',
                                    'timeout': 1})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.run()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
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
        expected_ret_val =  Utils.getDefaultEventDict({'received_from': '127.0.0.1', 'data': "Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever."})
        self.test_object.shutDown()
        # Give server some time to shut socket down.
        time.sleep(.1)
        for event in self.receiver.getEvent():
            self.assertEquals(event, expected_ret_val)

if __name__ == '__main__':
    unittest.main()