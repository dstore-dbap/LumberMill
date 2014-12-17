import sys
import time
import extendSysPath
import ModuleBaseTestCase
import socket
import netifaces
import mock
import Sniffer


class TestSniffer(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestSniffer, self).setUp(Sniffer.Sniffer(gp=mock.Mock()))
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind(('127.0.0.1', 0))
            self.port = self.server_socket.getsockname()[1]
            self.server_socket.listen(5)
        except:
            etype, evalue, etb = sys.exc_info()
            print("Could not create server socket. Exception: %s, Error: %s." % (etype, evalue))
            sys.exit()
        # Get loopback device name.
        self.loopback_interface_name = None
        for interface_name in netifaces.interfaces():
            if 'lo' not in interface_name:
                continue
            self.loopback_interface_name = interface_name
        self.assertIsNot(self.loopback_interface_name, None, "Needs loopback interface for testing.")

    def testTcpPacket(self):
        self.test_object.configure({'interface': self.loopback_interface_name,
                                    'packetfilter': 'port %s' % self.port})
        self.test_object.start()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.port))
        s.send('TestData\n')
        time.sleep(.5)
        #self.assertEqual(len(self.receiver.events), 6, "Exepcted packet count of 6.")


    def tearDown(self):
        self.server_socket.close()

