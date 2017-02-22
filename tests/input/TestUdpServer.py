import time
import mock
import socket
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.input import UdpServer


class TestUdpServer(ModuleBaseTestCase):

    def setUp(self):
        super(TestUdpServer, self).setUp(UdpServer.UdpServer(mock.Mock()))

    """
    - UdpServer:
        ipaddress:                       # <default: ''; type: string; is: optional>
        port:                            # <default: 5151; type: integer; is: optional>
        timeout:                         # <default: None; type: None||integer; is: optional>
        tls:                             # <default: False; type: boolean; is: optional>
        key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
        cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
        receivers:
          - NextModule
    """

    def test(self):
        self.test_object.configure({})
        self.checkConfiguration()
        self.test_object.start()
        # Give server process time to startup.
        time.sleep(.1)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        for _ in range(0, 100):
            s.sendto("Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever.", ('127.0.0.1', self.test_object.getConfigurationValue('port')))
        s.close()
        expected_ret_val = DictUtils.getDefaultEventDict({'data': "Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever."})
        expected_ret_val.pop('lumbermill')
        event = False
        time.sleep(2)
        counter = 0
        for event in self.receiver.getEvent():
            counter += 1
        self.assertTrue(event != False)
        self.assertEqual(counter, 100)
        event.pop('lumbermill')
        self.assertDictEqual(event, expected_ret_val)


    def tearDown(self):
        self.test_object.shutDown()
        ModuleBaseTestCase.tearDown(self)