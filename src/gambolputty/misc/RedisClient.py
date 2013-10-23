# -*- coding: utf-8 -*-
import redis
import BaseModule

class RedisClient(BaseModule.BaseModule):

    def setup(self):
        # Call parent setup method
        super(RedisClient, self).setup()
        self.default_redis_port = 6379
        self.default_redis_server = 'localhost'

    def configure(self, configuration):
         # Call parent configure method
        super(RedisClient, self).configure(configuration)
        if 'server' in configuration:
            redis_server, _, redis_port = configuration['server'].partition(":")
        try:
            self.redis_server = redis_server if redis_server != "" else self.default_redis_server
            self.redis_port = int(redis_port) if redis_port != "" else self.default_redis_port
            self.redis_client = redis.StrictRedis(host=self.redis_server, port=self.redis_port, db=0)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not connect to redis store at %s. Excpeption: %s, Error: %s." % (configuration['server'],etype, evalue))

    def getClient(self):
        return self.redis_client