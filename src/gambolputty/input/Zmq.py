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

    server: Server to poll. Pattern: hostname:port.
    pattern: Either pull or sub.
    mode: Whether to run a server or client.
    hwm: Highwatermark for receiving socket.

    Configuration template:

    - Zmq:
        server:                     # <default: 'localhost:5570'; type: string; is: optional>
        pattern:                    # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
        mode:                       # <default: 'connect'; type: string; values: ['connect', 'bind']; is: optional>
        topic:                      # <default: ''; type: string; is: optional>
        hwm:                        # <default: None; type: None||integer; is: optional>
        receivers:
          - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = False

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.client = None
        self.topic = self.getConfigurationValue('topic')
        self.zmq_context = zmq.Context()
        if self.getConfigurationValue('pattern') == 'pull':
            self.client = self.zmq_context.socket(zmq.PULL)
        else:
            self.client = self.zmq_context.socket(zmq.SUB)
            self.client.setsockopt(zmq.SUBSCRIBE, str(self.topic))
        if self.getConfigurationValue('hwm'):
            try:
                self.client.setsockopt(zmq.RCVHWM, self.getConfigurationValue('hwm'))
            except:
                self.client.setsockopt(zmq.HWM, self.getConfigurationValue('hwm'))
        server_name, server_port = self.getConfigurationValue('server').split(":")
        try:
            server_addr = socket.gethostbyname(server_name)
        except socket.gaierror:
            server_addr = server_name
        try:
            if self.getConfigurationValue('mode') == 'connect':
                self.client.connect('tcp://%s:%s' % (server_addr, server_port))
            else:
                self.client.bind('tcp://%s:%s' % (server_addr, server_port))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not connect to zeromq at %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue('server'), etype, evalue, Utils.AnsiColors.ENDC))
            self.gp.shutDown()

    def getEventFromInputQueue(self):
        try:
            event = self.client.recv()
            if self.topic:
                topic, event = event.split(' ', 1)
            return event
        except zmq.error.ContextTerminated:
            pass
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            if exc_value in ['Interrupted system call', 'Socket operation on non-socket']:
                return
            if type(exc_value) != 'Socket operation on non-socket':
                print "############%s###############" % exc_value
            self.logger.error("%sCould not read data from zeromq. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, exc_type, exc_value, Utils.AnsiColors.ENDC))

    def handleEvent(self, event):
        event = {"data": event}
        if self.topic:
            event['zmq_topic'] = self.topic
        yield Utils.getDefaultEventDict(event, caller_class_name=self.__class__.__name__)

    def shutDown(self):
        try:
            self.client.close()
            self.zmq_context.term()
        except AttributeError:
            pass
        # Call parent shutDown method.
        BaseThreadedModule.BaseThreadedModule.shutDown(self)
