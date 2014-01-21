# -*- coding: utf-8 -*-
import pprint
import sys
import redis
import cPickle
import BaseModule
from Decorators import ModuleDocstringParser
import Utils

@ModuleDocstringParser
class RedisClient(BaseModule.BaseModule):
    """
    A simple wrapper around the redis python module.

    cluster: dictionary of redis masters as keys and pack_members as values.

    Configuration example:

    - module: RedisClient
      server: redis.server    # <default: 'localhost'; type: string; is: optional>
      cluster: { 'localhost:1010': ['localhost:1111']}    # <default: {}; type: dictionary; is: optional>
      port: 6379              # <default: 6379; type: integer; is: optional>
      db: 0                   # <default: 0; type: integer; is: optional>
      password: None          # <default: None; type: None||string; is: optional>
      socket_timeout: 10      # <default: 10; type: integer; is: optional>
      charset: 'utf-8'        # <default: 'utf-8'; type: string; is: optional>
      errors: 'strict'        # <default: 'strict'; type: string; is: optional>
      decode_responses: False # <default: False; type: boolean; is: optional>
      unix_socket_path: ''    # <default: ''; type: string; is: optional>
    """
    module_type = "stand_alone"
    """Set module type"""

    def configure(self, configuration):
         # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        if len(self.getConfigurationValue('cluster')) == 0:
            self.redis_client = self.getRedisClient()
        else:
            self.redis_client = self.getClusterRedisClient()

    def getRedisClient(self):
        try:
            redis_client = redis.StrictRedis(host=self.getConfigurationValue('server'),
                                              port=self.getConfigurationValue('port'),
                                              db=self.getConfigurationValue('db'),
                                              password=self.getConfigurationValue('password'),
                                              socket_timeout=self.getConfigurationValue('socket_timeout'),
                                              charset=self.getConfigurationValue('charset'),
                                              errors=self.getConfigurationValue('errors'),
                                              decode_responses=self.getConfigurationValue('decode_responses'),
                                              unix_socket_path=self.getConfigurationValue('unix_socket_path'))
            return redis_client
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not connect to redis store at %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue['server'], etype, evalue, Utils.AnsiColors.ENDC))

    def getClusterRedisClient(self):
        import rediscluster
        # TODO: Implement a locking mechnism for the cluster client.
        # Some modules like Facet depend on this.
        cluster = {'nodes': {}, 'master_of': {}}
        counter = 1
        for master_node, slave_nodes in self.getConfigurationValue('cluster').iteritems():
            master_node_key = "node_%d" % counter
            node_name_or_ip, node_port = self._parseRedisServerAddress(master_node)
            cluster['nodes'].update({master_node_key: {'host':node_name_or_ip, 'port': node_port}})
            if 'default_node' not in cluster:
                cluster['default_node'] = master_node
            if type(slave_nodes) is str:
                slave_nodes = [slave_nodes]
            for slave_node in slave_nodes:
                counter += 1
                slave_node_key = "node_%d" % counter
                node_name_or_ip, node_port = self._parseRedisServerAddress(slave_node)
                cluster['nodes'].update({slave_node_key: {'host':node_name_or_ip, 'port': node_port}})
                cluster['master_of'].update({master_node_key: slave_node_key})
        redis_client = rediscluster.StrictRedisCluster(cluster=cluster,
                                                       db=self.getConfigurationValue('db'))
        return redis_client

    def _parseRedisServerAddress(self, node_address):
        try:
            node_name_or_ip, node_port = node_address.split(":")
        except ValueError:
            node_name_or_ip = node_address
            node_port = self.getConfigurationValue('port')
        return (node_name_or_ip, node_port)

    def getClient(self):
        return self.redis_client

    def getLock(self, name, timeout=None, sleep=0.1):
        return self.redis_client.lock(name, timeout, sleep)

    def setValue(self, key, value, ttl=0, pickle=True):
        if pickle is True:
            try:
                value = cPickle.dumps(value)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sCould not store %s:%s in redis. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, key, value, etype, evalue, Utils.AnsiColors.ENDC))
                raise
        self.redis_client.setex(key, ttl, value)

    def getValue(self, key, unpickle=True):
        value = self.redis_client.get(key)
        if unpickle and value:
            try:
                value = cPickle.loads(value)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sCould not unpickle %s:%s from redis. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, key, value, etype, evalue, Utils.AnsiColors.ENDC))
                raise
        return value
