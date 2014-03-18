# -*- coding: utf-8 -*-
import pprint
import sys
import redis
import BaseMultiProcessModule
import Utils
import Decorators
import time


@Decorators.ModuleDocstringParser
class RedisListSink(BaseMultiProcessModule.BaseMultiProcessModule):
    """
    Subscribes to a redis channels/lists and passes incoming events to receivers.

    Configuration example:

    - RedisList:
        list:                     # <type: String; is: required>
        server:                   # <default: 'localhost'; type: string; is: optional>
        port:                     # <default: 6379; type: integer; is: optional>
        db:                       # <default: 0; type: integer; is: optional>
        password:                 # <default: None; type: None||string; is: optional>
        format:                   # <default: None; type: None||string; is: optional>
        store_interval_in_secs:   # <default: 5; type: integer; is: optional>
        batch_size:               # <default: 500; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""
    can_run_parallel = True

    def configure(self, configuration):
         # Call parent configure method
        BaseMultiProcessModule.BaseMultiProcessModule.configure(self, configuration)
        self.is_storing = False
        self.list = self.getConfigurationValue('list')
        self.client = redis.StrictRedis(host=self.getConfigurationValue('server'),
                                          port=self.getConfigurationValue('port'),
                                          password=self.getConfigurationValue('password'),
                                          db=self.getConfigurationValue('db'))
        try:
            self.client.ping()
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not connect to redis store at %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL,self.getConfigurationValue('server'),etype, evalue, Utils.AnsiColors.ENDC))
            self.gp.shutDown()

    def run(self):
        self.buffer = Utils.Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'))
        BaseMultiProcessModule.BaseMultiProcessModule.run(self)

    def storeData(self, buffered_data):
        try:
            self.client.rpush(self.list, *buffered_data)
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            self.logger.error("%sCould not add event to redis list %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.list, exc_type, exc_value, Utils.AnsiColors.ENDC))

    def handleEvent(self, event):
        if self.getConfigurationValue('format'):
            publish_data = self.getConfigurationValue('format', event)
        else:
            publish_data = event
        self.buffer.append(publish_data)
        yield None