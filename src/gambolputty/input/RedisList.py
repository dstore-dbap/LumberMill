# -*- coding: utf-8 -*-
import sys
import redis
import BaseThreadedModule
import Utils
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class RedisList(BaseThreadedModule.BaseThreadedModule):
    """
    Subscribes to a redis channels/lists and passes incoming events to receivers.

    Configuration example:

    - module: RedisList
      lists: ['my_list']          # <type: list; is: required>
      server: redis.server        # <default: 'localhost'; type: string; is: optional>
      port: 6379                  # <default: 6379; type: integer; is: optional>
      db: 0                       # <default: 0; type: integer; is: optional>
      password: None              # <default: None; type: None||string; is: optional>
      timeout: 10                 # <default: 0; type: integer; is: optional>
    """

    module_type = "input"
    """Set module type"""

    can_run_parallel = True

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.lists = self.getConfigurationValue('lists')
        self.timeout = self.getConfigurationValue('timeout')
        try:
            self.client = redis.Redis(host=self.getConfigurationValue('server'),
                                      port=self.getConfigurationValue('port'),
                                      password=self.getConfigurationValue('password'),
                                      db=self.getConfigurationValue('db'))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not connect to redis store at %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL,self.getConfigurationValue('server'),etype, evalue, Utils.AnsiColors.ENDC))

    def getEventFromInputQueue(self):
        try:
            event = self.client.blpop(self.lists, timeout=self.timeout)
            return event
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            self.logger.error("%sCould not read data from redis list(s) %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.lists, exc_type, exc_value, Utils.AnsiColors.ENDC))

    def handleEvent(self, event):
        yield Utils.getDefaultEventDict(dict={"received_from": '%s' % (event[0]), "data": event[1]}, caller_class_name=self.__class__.__name__)