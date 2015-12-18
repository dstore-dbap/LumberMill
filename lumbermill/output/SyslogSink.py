# -*- coding: utf-8 -*-
import logging
import logging.handlers
import os
import socket

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser
from lumbermill.utils.DynamicValues import mapDynamicValue


@ModuleDocstringParser
class SyslogSink(BaseThreadedModule):
    """
    Send events to syslog.

    format: Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'. If not set the whole event dict is send.
    address: Either a server:port pattern or a filepath to a unix socket, e.g. /dev/log.
    proto: Protocol to use.
    facility: Syslog facility to use. List of possible values, @see: http://epydoc.sourceforge.net/stdlib/logging.handlers.SysLogHandler-class.html#facility_names

    Configuration template:

    - SyslogSink:
       format:                          # <type: string; is: required>
       address:                         # <default: 'localhost:514'; type: string; is: required>
       proto:                           # <default: 'tcp'; type: string; values: ['tcp', 'udp']; is: optional>
       facility:                        # <default: 'user'; type: string; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.syslogger = logging.getLogger(self.__class__.__name__)
        self.syslogger.propagate = False
        self.format = self.getConfigurationValue('format')
        if os.path.exists(self.getConfigurationValue('address')):
            address = self.getConfigurationValue('address')
        else:
            server, port = self.getConfigurationValue('address').split(':')
            address = (server, int(port))
        if self.getConfigurationValue('proto') == 'tcp':
            socket_type = socket.SOCK_STREAM
        else:
            socket_type = socket.SOCK_DGRAM
        try:
            facility = logging.handlers.SysLogHandler.facility_names[self.getConfigurationValue('facility')]
        except KeyError:
            self.logger.error("The configured facility %s is unknown." % (self.getConfigurationValue('facility')))
        self.syslog_handler = logging.handlers.SysLogHandler(address, facility=facility, socktype=socket_type)
        self.syslogger.addHandler(self.syslog_handler)
        self.format = self.getConfigurationValue('format')

    def handleEvent(self, event):
        if self.format:
            self.syslogger.info(mapDynamicValue(self.format, event))
        else:
            self.syslogger.info(event)
        yield None

    def shutDown(self):
        self.syslog_handler.close()
        BaseThreadedModule.shutDown(self)
