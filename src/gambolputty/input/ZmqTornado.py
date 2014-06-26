# -*- coding: utf-8 -*-
import socket
import sys
import zmq
import BaseModule
import Utils
from Decorators import ModuleDocstringParser
from zmq.eventloop import ioloop, zmqstream
ioloop.install()

@ModuleDocstringParser
class ZmqTornado(BaseModule.BaseModule):
    """
    Read events from a zeromq.

    servers: Servers to poll. Pattern: hostname:port.
    pattern: Either pull or sub.
    mode: Whether to run a server or client.
    separator: When using the sub pattern, messages can have a topic. Set separator to split message from topic.

    Configuration example:

    - Zmq:
        servers:                    # <default: ['localhost:5570']; type: list; is: optional>
        pattern:                    # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
        mode:                       # <default: 'connect'; type: string; values: ['connect', 'bind']; is: optional>
        topic:                      # <default: ''; type: string; is: optional>
        separator:                  # <default: None; type: None||string; is: optional>
    """

    module_type = "input"
    """Set module type"""
    can_run_parallel = False

    def configure(self, configuration):
         # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.client = None
        self.topic = self.getConfigurationValue('topic')
        self.separator = self.getConfigurationValue('separator')
        self.zmq_context = zmq.Context()
        if self.getConfigurationValue('pattern') == 'pull':
            self.client = self.zmq_context.socket(zmq.PULL)
        else:
            self.client = self.zmq_context.socket(zmq.SUB)
            self.client.setsockopt(zmq.SUBSCRIBE, str(self.topic))
        self.mode = self.getConfigurationValue('mode')
        for server in self.getConfigurationValue('servers'):
            server_name, server_port = server.split(":")
            try:
                server_addr = socket.gethostbyname(server_name)
            except socket.gaierror:
                server_addr = server_name
            try:
                if self.mode == 'connect':
                    self.client.connect('tcp://%s:%s' % (server_addr, server_port))
                else:
                    self.client.bind('tcp://%s:%s' % (server_addr, server_port))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sCould not connect to zeromq at %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, server, etype, evalue, Utils.AnsiColors.ENDC))
                self.gp.shutDown()
            self.client = zmqstream.ZMQStream(self.client)
            self.client.on_recv(self.onReceive)

    def onReceive(self, data):
        data = data[0]
        if self.separator:
            topic, data = data.split(self.separator)
        event = Utils.getDefaultEventDict({"data": data}, caller_class_name="ZmqTornado")
        self.sendEvent(event)

    def shutDown(self, silent=False):
        try:
            self.client.close()
            self.zmq_context.term()
        except AttributeError:
            pass