# -*- coding: utf-8 -*-
import sys
import socket

from lumbermill.constants import IS_PYPY
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Buffers import Buffer
from lumbermill.utils.Decorators import ModuleDocstringParser
from lumbermill.utils.DynamicValues import mapDynamicValue

# For pypy the default json module is the fastest.
if IS_PYPY:
    import json
else:
    json = False
    for module_name in ['ujson', 'yajl', 'simplejson', 'json']:
        try:
            json = __import__(module_name)
            break
        except ImportError:
            pass
    if not json:
        raise ImportError

@ModuleDocstringParser
class Udp(BaseThreadedModule):
    """
    Send events to udp socket.

    address: address:port
    format: Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'. If not set the whole event dict is send.
    store_interval_in_secs: Send data to redis in x seconds intervals.
    batch_size: Send data to redis if event count is above, even if store_interval_in_secs is not reached.
    backlog_size: Maximum count of events waiting for transmission. Events above count will be dropped.

    Configuration template:

    - output.Udp:
       address:                         # <default: 'localhost:514'; type: string; is: required>
       format:                          # <default: None; type: None||string; is: optional>
       store_interval_in_secs:          # <default: 5; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 500; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.format = self.getConfigurationValue('format')
        server, port = self.getConfigurationValue('address').split(':')
        self.target_address = (server, int(port))
        self.buffer = None
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            self.logger.error("Could not create udp socket to %s. Exception: %s, Error: %s." % (self.getConfigurationValue('address'), exc_type, exc_value))
            self.lumbermill.shutDown()

    def getStartMessage(self):
        return "Sending to %s in % batches. Max buffer size: %d" % (self.getConfigurationValue('address'),
                                                                    self.getConfigurationValue('batch_size'),
                                                                    self.getConfigurationValue('backlog_size'))

    def handleEvent(self, event):
        if self.format:
            publish_data = mapDynamicValue(self.format, event).encode('utf-8')
        else:
            publish_data = json.dumps(event).encode('utf-8')
        publish_data += "\n".encode('utf-8')
        try:
            self.socket.sendto(publish_data, self.target_address)
            return True
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            self.logger.error("Could not add event to %s. Exception: %s, Error: %s." % (self.target_address, exc_type, exc_value))
            return False
        yield None