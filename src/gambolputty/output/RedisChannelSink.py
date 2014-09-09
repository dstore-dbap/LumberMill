# -*- coding: utf-8 -*-
import sys
import redis
import BaseMultiProcessModule
import Utils
import Decorators


@Decorators.ModuleDocstringParser
class RedisChannelSink(BaseMultiProcessModule.BaseMultiProcessModule):
    """
    Publish incoming events to redis channel.

    channel: Name of redis channel to send data to.
    server: Redis server to connect to.
    port: Port redis server is listening on.
    db: Redis db.
    password: Redis password.
    format: Which event fields to send on, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'. If not set, the whole event dict is send.

    Configuration example:

    - RedisChannelSink:
        channel:                    # <type: string; is: required>
        server:                     # <default: 'localhost'; type: string; is: optional>
        port:                       # <default: 6379; type: integer; is: optional>
        db:                         # <default: 0; type: integer; is: optional>
        password:                   # <default: None; type: None||string; is: optional>
        format:                     # <default: None; type: None||string; is: optional>
        store_interval_in_secs:     # <default: 5; type: integer; is: optional>
        batch_size:                 # <default: 500; type: integer; is: optional>
        backlog_size:               # <default: 5000; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
         # Call parent configure method
        BaseMultiProcessModule.BaseMultiProcessModule.configure(self, configuration)
        self.format = self.getConfigurationValue('format')
        try:
            self.client = redis.Redis(host=self.getConfigurationValue('server'),
                                      port=self.getConfigurationValue('port'),
                                      password=self.getConfigurationValue('password'),
                                      db=self.getConfigurationValue('db'))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not connect to redis store at %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL,self.getConfigurationValue('server'),etype, evalue, Utils.AnsiColors.ENDC))

    def prepareRun(self):
        #self.buffer = Utils.Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))
        BaseMultiProcessModule.BaseMultiProcessModule.prepareRun(self)

    def handleEvent(self, event):
        if self.format:
            publish_data = Utils.mapDynamicValue(self.format, event)
        else:
            publish_data = event
        try:
            self.client.publish(self.getConfigurationValue('channel', event), publish_event)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not publish event to redis channel %s at %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL,self.getConfigurationValue('channel', event), self.getConfigurationValue('server'), etype, evalue, Utils.AnsiColors.ENDC))
        yield None

    def __handleEvent(self, event):
        if self.format:
            publish_data = Utils.mapDynamicValue(self.format, event)
        else:
            publish_data = event
        self.buffer.append(publish_data)
        yield None