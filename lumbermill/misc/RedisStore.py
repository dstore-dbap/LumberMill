# -*- coding: utf-8 -*-
import sys
import redis
import cPickle

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class RedisStore(BaseThreadedModule):
    """
    A simple wrapper around the redis python module.

    It can be used to store results of modules in a redis key/value store.

        server: Redis server to connect to.
        cluster: Dictionary of redis masters as keys and pack_followers as values, e.g.: {'172.16.0.1:6379': '172.16.0.2:6379'}
        port: Port redis server is listening on.
        db: Redis db.
        password: Redis password.
        socket_timeout: Socket timeout in seconds.
        charset: Charset to use.
        errors: tbd.
        decode_responses: specifies whether return values from Redis commands get decoded automatically using the client's charset value.
        unix_socket_path: Path to unix socket file.

    When set, the following options cause RedisStore to use a buffer for setting values.
    Multiple values are set via the pipe command, which speeds up storage. Still this comes at a price.
    Buffered values, that have not yet been send to redis, will be lost when LumberMill crashes.

        store_interval_in_secs: Sending data to redis in x seconds intervals.
        batch_size: Sending data to redis if count is above, even if store_interval_in_secs is not reached.
        backlog_size: Maximum count of values waiting for transmission. Values above count will be dropped.

    Configuration template:

    - RedisStore:
       server:                         # <default: 'localhost'; type: string; is: optional>
       cluster:                        # <default: {}; type: dictionary; is: optional>
       port:                           # <default: 6379; type: integer; is: optional>
       db:                             # <default: 0; type: integer; is: optional>
       password:                       # <default: None; type: None||string; is: optional>
       socket_timeout:                 # <default: 10; type: integer; is: optional>
       charset:                        # <default: 'utf-8'; type: string; is: optional>
       errors:                         # <default: 'strict'; type: string; is: optional>
       decode_responses:               # <default: False; type: boolean; is: optional>
       unix_socket_path:               # <default: None; type: None||string; is: optional>
       batch_size:                     # <default: None; type: None||integer; is: optional>
       store_interval_in_secs:         # <default: None; type: None||integer; is: optional>
       backlog_size:                   # <default: 5000; type: integer; is: optional>
    """
    module_type = "stand_alone"
    """Set module type"""

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        if len(self.getConfigurationValue('cluster')) == 0:
            redis_store = self.getConfigurationValue('server')
            self.client = self.getRedisClient()
        else:
            redis_store = self.getConfigurationValue('cluster')
            self.client = self.getClusterRedisClient()
        try:
            self.client.ping()
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not connect to redis store at %s. Exception: %s, Error: %s." % (redis_store,etype, evalue))
            self.lumbermill.shutDown()
        self.set_buffer = None
        if self.getConfigurationValue('store_interval_in_secs') or self.getConfigurationValue('batch_size'):
            self.set_buffer = Utils.Buffer(self.getConfigurationValue('batch_size'), self.setBufferedCallback, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))
            self._set = self.set
            self.set = self.setBuffered
            self._get = self.get
            self.get = self.getBuffered
            self._delete = self.delete
            self.delete = self.deleteBuffered
            self._pop = self.pop
            self.pop = self.popBuffered

    def getRedisClient(self):
        try:
            client = redis.StrictRedis(host=self.getConfigurationValue('server'),
                                       port=self.getConfigurationValue('port'),
                                       db=self.getConfigurationValue('db'),
                                       password=self.getConfigurationValue('password'),
                                       socket_timeout=self.getConfigurationValue('socket_timeout'),
                                       charset=self.getConfigurationValue('charset'),
                                       errors=self.getConfigurationValue('errors'),
                                       decode_responses=self.getConfigurationValue('decode_responses'),
                                       unix_socket_path=self.getConfigurationValue('unix_socket_path'))
            return client
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not connect to redis store at %s. Exception: %s, Error: %s." % (self.getConfigurationValue['server'], etype, evalue))

    def getClusterRedisClient(self):
        import rediscluster
        # TODO: Implement a locking mechnism for the cluster client.
        # Some modules like Facet depend on this.
        cluster = {'nodes': {}, 'master_of': {}}
        counter = 1
        for master_node, slave_nodes in self.getConfigurationValue('cluster').items():
            master_node_key = "node_%d" % counter
            node_name_or_ip, node_port = self._parseRedisServerAddress(master_node)
            cluster['nodes'].update({master_node_key: {'host':node_name_or_ip, 'port': node_port}})
            #if 'default_node' not in cluster:
            #    cluster['default_node'] = master_node
            if type(slave_nodes) is str:
                slave_nodes = [slave_nodes]
            for slave_node in slave_nodes:
                counter += 1
                slave_node_key = "node_%d" % counter
                node_name_or_ip, node_port = self._parseRedisServerAddress(slave_node)
                cluster['nodes'].update({slave_node_key: {'host':node_name_or_ip, 'port': node_port}})
                #cluster['master_of'].update({master_node_key: slave_node_key})
        client = rediscluster.StrictRedisCluster(cluster=cluster,
                                                 db=self.getConfigurationValue('db'))
        return client

    def _parseRedisServerAddress(self, node_address):
        try:
            node_name_or_ip, node_port = node_address.split(":")
        except ValueError:
            node_name_or_ip = node_address
            node_port = self.getConfigurationValue('port')
        return (node_name_or_ip, node_port)

    def getClient(self):
        return self.client

    def getLock(self, name, timeout=None, sleep=0.1):
        return self.client.lock(name, timeout, sleep)

    def set(self, key, value, ttl=0, pickle=True):
        if pickle is True:
            try:
                value = cPickle.dumps(value)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not store %s:%s in redis. Exception: %s, Error: %s." % (key, value, etype, evalue))
                raise
        if ttl:
            self.client.setex(key, ttl, value)
        else:
            self.client.set(key, value)

    def setBuffered(self, key, value, ttl=0, pickle=True):
        if pickle is True:
            try:
                value = cPickle.dumps(value)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not store %s:%s in redis. Exception: %s, Error: %s." % (key, value, etype, evalue))
                raise
        if ttl:
            self.set_buffer.append({'key':key, 'ttl': ttl, 'value': value})
        else:
            self.set_buffer.append({'key':key, 'value': value})

    def setBufferedCallback(self, values):
        pipe = self.client.pipeline()
        for value in values:
            if 'ttl' in value:
                pipe.setex(value['key'], value['ttl'], value['value'])
            else:
                pipe.set(value['key'], value['value'])
        try:
            pipe.execute()
            return True
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not flush buffer. Exception: %s, Error: %s." % (etype, evalue))


    def get(self, key, unpickle=True):
        value = self.client.get(key)
        if unpickle and value:
            try:
                value = cPickle.loads(value)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not unpickle %s:%s from redis. Exception: %s, Error: %s." % (key, value, etype, evalue))
                raise
        return value

    def getBuffered(self, key, unpickle=True):
        try:
            value_idx = next(index for (index, entry) in enumerate(self.set_buffer.buffer) if entry["key"] == key)
            return self.set_buffer.buffer[value_idx]
        except:
            return self._get(key, unpickle)

    def delete(self, key):
        self.client.delete(key)

    def deleteBuffered(self, key):
        try:
            value_idx = next(index for (index, entry) in enumerate(self.set_buffer.buffer) if entry["key"] == key)
            self.set_buffer.buffer.pop(value_idx)
            return
        except:
            self._delete(key)

    def pop(self, key, unpickle=True):
        value = self.get(key, unpickle)
        if value:
            self.delete(key)
        return value

    def popBuffered(self, key, unpickle=True):
        try:
            value_idx = next(index for (index, entry) in enumerate(self.set_buffer.buffer) if entry["key"] == key)
            return self.set_buffer.buffer.pop(value_idx)
        except:
            return self._pop(key, unpickle)

    def shutDown(self):
        try:
            self.buffer.flush()
        except:
            pass
        BaseThreadedModule.shutDown(self)
