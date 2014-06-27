# -*- coding: utf-8 -*-
import sys
import zmq
import socket
import msgpack
import BaseMultiProcessModule
import Utils
import Decorators

@Decorators.ModuleDocstringParser
class ZmqSink(BaseMultiProcessModule.BaseMultiProcessModule):
    """
    Sends events to zeromq.

    server: Server to connect to. Pattern: hostname:port.
    pattern: Either push or pub.
    mode: Whether to run a server or client. If running as server, pool size is restricted to a single process.
    topic: The channels topic.
    hwm: Highwatermark for sending socket.
    format: Which event fields to send on, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'. If not set the whole event dict is send msgpacked.
    store_interval_in_secs: Send data to redis in x seconds intervals.
    batch_size: Send data to redis if event count is above, even if store_interval_in_secs is not reached.
    backlog_size: Maximum count of events waiting for transmission. Events above count will be dropped.

    Configuration example:

    - ZmqSink:
        server:                     # <default: 'localhost:5570'; type: string; is: optional>
        pattern:                    # <default: 'push'; type: string; values: ['push', 'pub']; is: optional>
        mode:                       # <default: 'connect'; type: string; values: ['connect', 'bind']; is: optional>
        topic:                      # <default: None; type: None||string; is: optional>
        hwm:                        # <default: None; type: None||integer; is: optional>
        format:                     # <default: None; type: None||string; is: optional>
        store_interval_in_secs:     # <default: 5; type: integer; is: optional>
        batch_size:                 # <default: 500; type: integer; is: optional>
        backlog_size:               # <default: 5000; type: integer; is: optional>
    """

    module_type = "input"
    """Set module type"""
    can_run_parallel = True

    def configure(self, configuration):
         # Call parent configure method
        BaseMultiProcessModule.BaseMultiProcessModule.configure(self, configuration)
        self.server = None
        self.topic = self.getConfigurationValue('topic')
        self.format = self.getConfigurationValue('format')
        self.mode = self.getConfigurationValue('mode')
        if self.mode == "bind":
            self.can_run_parallel = False

    def initZmqContext(self):
        self.zmq_context = zmq.Context()
        if self.getConfigurationValue('pattern') == 'push':
            self.client = self.zmq_context.socket(zmq.PUSH)
        else:
            self.client = self.zmq_context.socket(zmq.PUB)
        if self.getConfigurationValue('hwm'):
            try:
                self.client.setsockopt(zmq.SNDHWM, self.getConfigurationValue('hwm'))
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

    def run(self):
        self.initZmqContext()
        self.buffer = Utils.Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))
        BaseMultiProcessModule.BaseMultiProcessModule.run(self)

    def storeData(self, buffered_data):
        try:
            for data in buffered_data:
                #print "Sending %s.\n" % data
                self.client.send("%s" % data)
            return True
        except zmq.error.ContextTerminated:
            pass
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            if exc_value in ['Interrupted system call', 'Socket operation on non-socket']:
                return False
            self.logger.error("%sCould not add events to zmq. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, exc_type, exc_value, Utils.AnsiColors.ENDC))
            return False

    def handleEvent(self, event):
        if self.format:
            publish_data = Utils.mapDynamicValue(self.format, event)
        else:
            publish_data = msgpack.packb(event)
        if self.topic:
             publish_data = "%s %s" % (self.topic, publish_data)
        self.buffer.append(publish_data)
        yield None

    def shutDown(self):
        try:
            self.client.close()
            self.zmq_context.term()
        except AttributeError:
            pass
        # Call parent shutDown method.
        BaseMultiProcessModule.BaseMultiProcessModule.shutDown(self)
