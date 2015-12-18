# -*- coding: utf-8 -*-
import sys

import redis

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser
from lumbermill.utils.DynamicValues import mapDynamicValue


@ModuleDocstringParser
class RedisChannelSink(BaseThreadedModule):
    """
    Publish incoming events to redis channel.

    channel: Name of redis channel to send data to.
    server: Redis server to connect to.
    port: Port redis server is listening on.
    db: Redis db.
    password: Redis password.
    format: Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'. If not set, the whole event dict is send.

    Configuration template:

    - RedisChannelSink:
       channel:                         # <type: string; is: required>
       server:                          # <default: 'localhost'; type: string; is: optional>
       port:                            # <default: 6379; type: integer; is: optional>
       db:                              # <default: 0; type: integer; is: optional>
       password:                        # <default: None; type: None||string; is: optional>
       format:                          # <default: None; type: None||string; is: optional>
       store_interval_in_secs:          # <default: 5; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 5000; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.format = self.getConfigurationValue('format')
        try:
            self.client = redis.Redis(host=self.getConfigurationValue('server'),
                                      port=self.getConfigurationValue('port'),
                                      password=self.getConfigurationValue('password'),
                                      db=self.getConfigurationValue('db'))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not connect to redis store at %s. Exception: %s, Error: %s." % (self.getConfigurationValue('server'),etype, evalue))

    def initAfterFork(self):
        #self.buffer = Utils.Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))
        BaseThreadedModule.initAfterFork(self)

    def handleEvent(self, event):
        if self.format:
            publish_data = mapDynamicValue(self.format, event)
        else:
            publish_data = event
        try:
            self.client.publish(self.getConfigurationValue('channel', event), publish_data)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not publish event to redis channel %s at %s. Exception: %s, Error: %s." % (self.getConfigurationValue('channel', event), self.getConfigurationValue('server'), etype, evalue))
        yield None

    def __handleEvent(self, event):
        if self.format:
            publish_data = mapDynamicValue(self.format, event)
        else:
            publish_data = event
        self.buffer.append(publish_data)
        yield None