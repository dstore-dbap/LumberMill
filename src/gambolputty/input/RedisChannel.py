# -*- coding: utf-8 -*-
import sys
from tornado import autoreload
import RedisAsyncClient
import BaseModule
import Utils
import Decorators


@Decorators.ModuleDocstringParser
class RedisChannel(BaseModule.BaseModule):
    """
    Subscribes to a redis channels and passes incoming events to receivers.

    channel: Name of redis channel to subscribe to.
    server: Redis server to connect to.
    port: Port redis server is listening on.
    db: Redis db.
    password: Redis password.

    Configuration template:

    - RedisChannel:
        channel:                    # <type: string; is: required>
        server:                     # <default: 'localhost'; type: string; is: optional>
        port:                       # <default: 6379; type: integer; is: optional>
        db:                         # <default: 0; type: integer; is: optional>
        password:                   # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = False

    def configure(self, configuration):
         # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        try:
            self.client = RedisAsyncClient.AsyncRedisClient(address=(self.getConfigurationValue('server'), self.getConfigurationValue('port')))
            if self.getConfigurationValue('db') != 0:
                self.client.fetch(('select', self.getConfigurationValue('db')), self.checkReply)
            if self.getConfigurationValue('password'):
                self.client.fetch(('select', self.getConfigurationValue('password')), self.checkReply)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not connect to redis store at %s. Excpeption: %s, Error: %s." % (self.getConfigurationValue('server'), etype, evalue))

    def run(self):
        if not self.receivers:
            self.logger.error("Will not start module %s since no receivers are set." % (self.__class__.__name__))
            return
        if not self.client:
            return
        try:
            self.client.fetch(('subscribe', self.getConfigurationValue('channel')), self.receiveEvent)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not fetch event from redis store at %s. Excpeption: %s, Error: %s." % (self.getConfigurationValue('server'), etype, evalue))
        autoreload.add_reload_hook(self.shutDown)
        #ioloop = IOLoop.instance()
        #ioloop.make_current()
        #try:
        #    ioloop.start()
        #except ValueError:
            # Ignore errors like "ValueError: I/O operation on closed kqueue fd". These might be thrown during a reload.
        #    pass

    def checkReply(self, answer):
        if answer != "OK":
            self.logger.error("Could not connect to server %s. Server said: %s." % (self.getConfigurationValue('server'), answer))
            self.gp.shutDown()

    def handleEvent(self, event):
        if event[0] != 'message':
            return
        yield Utils.getDefaultEventDict(dict={"received_from": '%s' % event[1], "data": event[2]}, caller_class_name=self.__class__.__name__)