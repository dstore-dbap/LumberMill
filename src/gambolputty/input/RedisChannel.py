# -*- coding: utf-8 -*-
import sys
import tornado
import RedisAsyncClient
import BaseThreadedModule
import Utils
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class RedisChannel(BaseThreadedModule.BaseThreadedModule):
    """
    Subscribes to a redis channel and passes incoming events to receivers.

    Configuration example:

    - module: RedisChannel
      configuration:
        channels:                    # <type: string; is: required>
        server: redis.server        # <default: 'localhost'; type: string; is: optional>
        port: 6379                  # <default: 6379; type: integer; is: optional>
        db: 0                       # <default: 0; type: integer; is: optional>
        password: None              # <default: None; type: None||string; is: optional>
        socket_timeout: 10          # <default: 10; type: integer; is: optional>
    """

    module_type = "input"
    """Set module type"""

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        try:
            self.client = RedisAsyncClient.AsyncRedisClient(address=(self.getConfigurationValue('server'),self.getConfigurationValue('port')), socket_timeout=self.getConfigurationValue('socket_timeout'))
            if self.getConfigurationValue('db') != 0:
                self.client.fetch(('select', self.getConfigurationValue('db')), self.checkReply)
            if self.getConfigurationValue('password'):
                self.client.fetch(('select', self.getConfigurationValue('password')), self.checkReply)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not connect to redis store at %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL,self.getConfigurationValue('server'),etype, evalue, Utils.AnsiColors.ENDC))

    def run(self):
        if not self.receivers:
            self.logger.error("%sWill not start module %s since no receivers are set.%s" % (Utils.AnsiColors.FAIL, self.__class__.__name__, Utils.AnsiColors.ENDC))
            return
        if not self.client:
            return
        self.client.fetch(('subscribe', self.getConfigurationValue('channels')), self.handleEvent)
        tornado.ioloop.IOLoop.instance().start()

    def checkReply(self, answer):
        if answer != "OK":
            self.logger.error("%sCould not subscribe to channel(s) %s.Server said: %s.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue('channels'), answer,Utils.AnsiColors.ENDC))
            self.gp.shutDown()

    def handleEvent(self, event):
        if event[0] != 'message':
            return
        self.sendEventToReceivers(Utils.getDefaultEventDict({"received_from": 'RedisChannel %s' % event[1], "data": event[2]}))