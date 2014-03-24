# -*- coding: utf-8 -*-
import sys
import redis
import BaseMultiProcessModule
import Utils
import Decorators

@Decorators.ModuleDocstringParser
class RedisListSink(BaseMultiProcessModule.BaseMultiProcessModule):
    """
    Send events to a redis lists.

    list: Name of redis list to send data to.
    server: Redis server to connect to.
    port: Port redis server is listening on.
    db: Redis db.
    password: Redis password.
    format: Which event fields to send on, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'. If not set the whole event dict is send.
    store_interval_in_secs: Send data to redis in x seconds intervals.
    batch_size: Send data to redis if event count is above, even if store_interval_in_secs is not reached.
    backlog_size: Maximum count of events waiting for transmission. Events above count will be dropped.

    Configuration example:

    - RedisListSink:
        list:                     # <type: String; is: required>
        server:                   # <default: 'localhost'; type: string; is: optional>
        port:                     # <default: 6379; type: integer; is: optional>
        db:                       # <default: 0; type: integer; is: optional>
        password:                 # <default: None; type: None||string; is: optional>
        format:                   # <default: None; type: None||string; is: optional>
        store_interval_in_secs:   # <default: 5; type: integer; is: optional>
        batch_size:               # <default: 500; type: integer; is: optional>
        backlog_size:             # <default: 5000; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""
    can_run_parallel = True

    def configure(self, configuration):
         # Call parent configure method
        BaseMultiProcessModule.BaseMultiProcessModule.configure(self, configuration)
        self.format = self.getConfigurationValue('format')
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
        self.buffer = Utils.Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))
        BaseMultiProcessModule.BaseMultiProcessModule.run(self)

    def storeData(self, buffered_data):
        try:
            self.client.rpush(self.list, *buffered_data)
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            self.logger.error("%sCould not add event to redis list %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.list, exc_type, exc_value, Utils.AnsiColors.ENDC))
            return False

    def handleEvent(self, event):
        if self.format:
            publish_data = self.getConfigurationValue('format', event)
        else:
            publish_data = event
        self.buffer.append(publish_data)
        yield None

    def shutDown(self, silent=False):
        try:
            self.buffer.flush()
        except:
            pass
        BaseMultiProcessModule.BaseMultiProcessModule.shutDown(self, silent)