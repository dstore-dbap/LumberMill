# -*- coding: utf-8 -*-
import sys
import redis
import BaseModule
from Decorators import GambolPuttyModule

@GambolPuttyModule
class RedisClient(BaseModule.BaseModule):
    """
    A simple wrapper around the redis python module.

    Configuration example:

    - module: RedisClient
      configuration:
        server: redis.server    # <default: 'localhost'; type: string; is: optional>
        port: 6379              # <default: 6379; type: integer; is: optional>
        db: 0                   # <default: 0; type: string; is: optional>
    """

    def configure(self, configuration):
         # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        try:
            self.redis_client = redis.StrictRedis(host=self.getConfigurationValue('server'), port=self.getConfigurationValue('port'), db=self.getConfigurationValue('db'))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not connect to redis store at %s. Excpeption: %s, Error: %s." % (configuration['server'],etype, evalue))

    def getClient(self):
        return self.redis_client