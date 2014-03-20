# -*- coding: utf-8 -*-
import sys
import Utils
import BaseMultiProcessModule
from Decorators import ModuleDocstringParser
import socket
import time

@ModuleDocstringParser
class GraphiteSink(BaseMultiProcessModule.BaseMultiProcessModule):
    """
    Send metrics to graphite server.

    server: Graphite server to connect to.
    port: Port carbon-cache is listening on.
    formats: Format of messages to send to graphite, e.g.: ['gambolputty.stats.event_rate_%(interval)ds %(event_rate)s'].
    store_interval_in_secs: Send data to graphite in x seconds intervals.
    batch_size: Send data to graphite if event count is above, even if store_interval_in_secs is not reached.
    backlog_size: Send count of events waiting for transmission. Events above count will be dropped.

    Configuration example:

    - GraphiteSink:
        server:                   # <default: 'localhost'; type: string; is: optional>
        port:                     # <default: 2003; type: integer; is: optional>
        formats:                  # <type: list; is: required>
        store_interval_in_secs:   # <default: 5; type: integer; is: optional>
        batch_size:               # <default: 1; type: integer; is: optional>
        backlog_size:             # <default: 5000; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseMultiProcessModule.BaseMultiProcessModule.configure(self, configuration)
        self.formats = self.getConfigurationValue('formats')
        self.connection_data = (self.getConfigurationValue('server'), self.getConfigurationValue('port'))
        self.connection = None

    def connect(self):
        # Connect to server
        connection = socket.socket()
        try:
            connection.connect(self.connection_data)
            return connection
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sFailed to connect to %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.connection_data, etype, evalue, Utils.AnsiColors.ENDC))
            return False

    def run(self):
        self.buffer = Utils.Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))
        self.connection = self.connect()
        if not self.connection:
            self.gp.shutDown()
            return
        BaseMultiProcessModule.BaseMultiProcessModule.run(self)

    def handleEvent(self, event):
        for format in self.formats:
            mapped_data = self.mapDynamicValue(format, event)
            if mapped_data:
                self.buffer.append("%s %s" % (mapped_data, int(time.time())))
                break
        yield None

    def storeData(self, events):
        for event in events:
            try:
                self.connection.send(event)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sServer communication error. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))
                tries = 0
                self.connection.close()
                self.connection = None
                while tries < 5 and not self.connection:
                    time.sleep(5)
                    self.logger.warning("%sTrying to reconnect to %s.%s" % (Utils.AnsiColors.WARNING, self.connection_data, Utils.AnsiColors.ENDC))
                    # Try to reconnect.
                    self.connection = self.connect()
                    tries += 1
                if not self.connection:
                    self.logger.error("%sReconnect failed. Shutting down.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))
                    self.gp.shutDown()
                else:
                    self.logger.info("%sReconnection to %s successful.%s" % (Utils.AnsiColors.LIGHTBLUE, self.connection_data, Utils.AnsiColors.ENDC))

    def shutDown(self, silent=False):
        if self.connection:
            self.connection.close()
        BaseMultiProcessModule.BaseMultiProcessModule.shutDown(self, silent)