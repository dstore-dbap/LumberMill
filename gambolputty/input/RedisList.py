# -*- coding: utf-8 -*-
import sys
import redis
import BaseThreadedModule
import Utils
import Decorators
import time


@Decorators.ModuleDocstringParser
class RedisList(BaseThreadedModule.BaseThreadedModule):
    """
    Subscribes to a redis channels/lists and passes incoming events to receivers.

    lists: Name of redis lists to subscribe to.
    server: Redis server to connect to.
    port: Port redis server is listening on.
    batch_size: Number of events to return from redis list.
    db: Redis db.
    password: Redis password.
    timeout: Timeout in seconds.

    Configuration template:

    - RedisList:
        lists:                    # <type: string||list; is: required>
        server:                   # <default: 'localhost'; type: string; is: optional>
        port:                     # <default: 6379; type: integer; is: optional>
        batch_size:               # <default: 1; type: integer; is: optional>
        db:                       # <default: 0; type: integer; is: optional>
        password:                 # <default: None; type: None||string; is: optional>
        timeout:                  # <default: 0; type: integer; is: optional>
        receivers:
          - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.redis_bulk_script = None
        self.lists = self.getConfigurationValue('lists')
        if not isinstance(self.lists, list):
            self.lists = [self.lists]
        self.timeout = self.getConfigurationValue('timeout')
        self.batch_size = self.getConfigurationValue('batch_size')
        self.client = redis.StrictRedis(host=self.getConfigurationValue('server'),
                                        port=self.getConfigurationValue('port'),
                                        password=self.getConfigurationValue('password'),
                                        db=self.getConfigurationValue('db'))
        try:
            self.client.ping()
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not connect to redis store at %s. Exception: %s, Error: %s." % (self.getConfigurationValue('server'), etype, evalue))
            self.gp.shutDown()
        # Monkeypatch run method to use the correct handle event method.
        if self.batch_size == 1:
            self.run = self.handleSingleEvent
        else:
            self.run = self.handleBatchEvents

    def run(self):
        self.logger.error("Monkeypatching the run method of RedisList seems to have failed.")
        self.gp.shutDown()

    def handleSingleEvent(self):
        while self.alive:
            event = None
            try:
                event = self.client.blpop(self.lists, timeout=self.timeout)
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.logger.error("Could not read data from redis list(s) %s. Exception: %s, Error: %s." % (self.lists, exc_type, exc_value))
            if event:
                event = Utils.getDefaultEventDict(dict={"received_from": '%s' % event[0], "data": event[1]}, caller_class_name=self.__class__.__name__)
                self.sendEvent(event)

    def handleBatchEvents(self):
        pipeline = self.client.pipeline()
        while self.alive:
            for _ in range(0, self.batch_size):
                pipeline.blpop(self.lists, timeout=self.timeout)
            try:
                events = pipeline.execute()
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.logger.error("Could not read data from redis list(s) %s. Exception: %s, Error: %s." % (self.lists, exc_type, exc_value))
                continue
            if not events:
                continue
            for event in events:
                event = Utils.getDefaultEventDict(dict={"received_from": '%s' % event[0], "data": event[1]}, caller_class_name=self.__class__.__name__)
                self.sendEvent(event)