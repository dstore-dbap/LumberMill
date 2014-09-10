import pprint
import extendSysPath
import ModuleBaseTestCase
import socket
import mock
import Utils
import NetSniffer
from scapy.all import *

class TestNetSniffer(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestNetSniffer, self).setUp(NetSniffer.NetSniffer(gp=mock.Mock()))

    def testTcpPacket(self):
        self.test_object.configure({'interface': ['lo']})
        ip=IP(src="127.0.0.1",dst="127.0.0.1")
        SYN=TCP(sport=40508,dport=40508,flags="S",seq=12345)
        send(ip/SYN)
        for event in self.receiver.getEvent():
            pprint.pprint(event)



