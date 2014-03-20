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
    format: Which event fields to send on, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'. If not set the whole event dict is send.

    Configuration example:

    - RedisChannelSink:
        channel:                    # <type: string; is: required>
        server:                     # <default: 'localhost'; type: string; is: optional>
        port:                       # <default: 6379; type: integer; is: optional>
        db:                         # <default: 0; type: integer; is: optional>
        password:                   # <default: None; type: None||string; is: optional>
        format:                     # <default: None; type: None||string; is: optional>
    """

    module_type = "output"
    """Set module type"""
    can_run_parallel = True

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

    def run(self):
        if not self.client:
            return
        BaseMultiProcessModule.BaseMultiProcessModule.run(self)

    def handleEvent(self, event):
        if self.format:
            publish_event = self.getConfigurationValue('format', event)
        else:
            publish_event = event
        try:
            self.client.publish(self.getConfigurationValue('channel', event), publish_event)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not publish event to redis channel %s at %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL,self.getConfigurationValue('channel', event), self.getConfigurationValue('server'), etype, evalue, Utils.AnsiColors.ENDC))
        yield None