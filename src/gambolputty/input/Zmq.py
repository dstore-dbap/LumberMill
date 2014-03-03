# -*- coding: utf-8 -*-
import socket
import sys
import zmq
import BaseThreadedModule
import Utils
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class Zmq(BaseThreadedModule.BaseThreadedModule):
    """
    Read events from a zeromq.

    servers: Servers to poll. Pattern: hostname:port.
    pattern: Either pull or subscribe.
    mode: Wether to run a server or client.
    multipart: When using the sub pattern, messages can have a topic. If send via multipart set this to true.
    seperator: When using the sub pattern, messages can have a topic. Set seperator to split message from topic.

    Configuration example:

    - Zmq:
        servers:                    # <default: ['localhost:5570']; type: list; is: optional>
        pattern:                    # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
        mode:                       # <default: 'connect'; type: string; values: ['connect', 'bind']; is: optional>
        topic:                      # <default: ''; type: string; is: optional>
        multipart:                  # <default: False; type: boolean; is: optional>
        seperator:                  # <default: None; type: None||string; is: optional>
    """

    module_type = "input"
    """Set module type"""
    can_run_parallel = False

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.receiver = None
        self.topic = self.getConfigurationValue('topic')
        self.multipart = self.getConfigurationValue('multipart')
        self.seperator = self.getConfigurationValue('seperator')
        self.zmq_context = zmq.Context()
        if self.getConfigurationValue('pattern') == 'pull':
            self.receiver = self.zmq_context.socket(zmq.PULL)
        else:
            self.receiver = self.zmq_context.socket(zmq.SUB)
            self.receiver.setsockopt(zmq.SUBSCRIBE, str(self.topic))
        mode = self.getConfigurationValue('mode')
        for server in self.getConfigurationValue('servers'):
            server_name, server_port = server.split(":")
            try:
                server_addr = socket.gethostbyname(server_name)
            except socket.gaierror:
                server_addr = server_name
            try:
                if mode == 'connect':
                    self.receiver.connect('tcp://%s:%s' % (server_addr, server_port))
                else:
                    self.receiver.bind('tcp://%s:%s' % (server_addr, server_port))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sCould not connect to zeromq at %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, server, etype, evalue, Utils.AnsiColors.ENDC))
                #self.gp.shutDown()

    def getEventFromInputQueue(self):
        try:
            if self.multipart:
                topic, event = self.receiver.recv_multipart()
            else:
                event = self.receiver.recv()
            if self.seperator:
                topic, event = event.split(self.seperator)
            return event
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            self.logger.error("%sCould not read data from zeromq. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, exc_type, exc_value, Utils.AnsiColors.ENDC))

    def handleEvent(self, event):
        yield Utils.getDefaultEventDict(dict={"received_from": '%s' % (event[0]), "data": event}, caller_class_name=self.__class__.__name__)

    def shutDown(self, silent=False):
        # Call parent shutDown method.
        BaseThreadedModule.BaseThreadedModule.shutDown(self, silent)
        return
        try:
            self.receiver.close()
            self.zmq_context.term()
        except AttributeError:
            pass