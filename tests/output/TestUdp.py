import time
import sys
import socketserver
import threading
import json

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from tests.ServiceDiscovery import getFreeUdpPortoOnLocalhost
import lumbermill.utils.DictUtils as DictUtils
from lumbermill.output import Udp

class UDPHandler(socketserver.DatagramRequestHandler):

    def __init__(self, test_class_instance, *args, **keys):
        self.test_class_instance = test_class_instance
        socketserver.BaseRequestHandler.__init__(self, *args, **keys)

    def handle(self):
        received_message = self.rfile.readline().strip()
        self.test_class_instance.received_message = received_message

class UdpRequestHandlerFactory:
    def produce(self, udp_server_instance):
        def createHandler(*args, **keys):
            return UDPHandler(udp_server_instance, *args, **keys)
        return createHandler

class TestUdp(ModuleBaseTestCase):

    def setUp(self):
        super(TestUdp, self).setUp(Udp.Udp(MockLumberMill()))
        self.received_message = None
        ipaddr, port = getFreeUdpPortoOnLocalhost()
        self.address = (ipaddr, port)
        try:
            self.udp_server = socketserver.UDPServer(self.address, UdpRequestHandlerFactory().produce(self))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not listen on %s. Exception: %s, Error: %s" % (self.address, etype, evalue))
            return
        server_thread = threading.Thread(target=self.udp_server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    """
    - output.Udp:
        address:                         # <default: 'localhost:514'; type: string; is: required>
        format:                          # <default: None; type: None||string; is: optional>
        store_interval_in_secs:          # <default: 5; type: integer; is: optional>
        batch_size:                      # <default: 500; type: integer; is: optional>
        backlog_size:                    # <default: 500; type: integer; is: optional>
    """

    def test(self):
        self.test_object.configure({"address": f"{self.address[0]}:{self.address[1]}", "batch_size": 1})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        event = DictUtils.getDefaultEventDict({'data': 'One thing is for sure; a sheep is not a creature of the air.'})
        for _ in range(0, 2):
            self.test_object.receiveEvent(event)
        time.sleep(.5)
        received_message_json = json.loads(self.received_message)
        self.assertEqual(received_message_json['data'], 'One thing is for sure; a sheep is not a creature of the air.')

    def tearDown(self):
        self.udp_server.shutdown()
        self.udp_server.server_close()
        self.test_object.shutDown()
        ModuleBaseTestCase.tearDown(self)