# -*- coding: utf-8 -*-
import inspect
import re
import socket
import Utils
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class TrackEvents(BaseThreadedModule.BaseThreadedModule):
    """

    Keeps track of all events passing through GambolPutty.

    This module stores all events that enter GambolPutty in a redis backend and deletes them, as soon as they
    get destroyed by the BaseModule.destroyEvent method. Events that did not get destroyed will be resent when
    GamboPutty is restarted. This should make sure that nearly every event gets to its destination, even when
    something goes absolutely wrong.

    As storage backend a redis client is needed.

    Please note, that this will significantly slow down the event processing. You have to decide if speed or
    event delivery is of higher importance to you. Even without this module, GambolPutty tries to make sure
    all events reach their destination. This module is thread based, so playing around with its pool size might
    increase performance.

    !!IMPORTANT!!: At the moment, this module will only work with TcpServerTornado as input.

    Configuration example:

    - module: TrackEvents
      pool_size: 1
      configuration:
        redis_client: RedisClientName           # <type: string; is: required>
        redis_ttl: 3600
    """

    module_type = "stand_alone"
    """Set module type"""

    input_queue = False
    callback_registered = {}
    main_thread = False

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.class_name_re = re.compile("'(.*)'")
        self.redis_key_prefix = 'TrackEvents:%s' % socket.gethostname()
        if not TrackEvents.main_thread:
            TrackEvents.main_thread = self
            TrackEvents.input_queue = self.gp.produceQueue(self)
        self.input_queue = TrackEvents.input_queue

    def register(self):
        # Get all input modules an register ourself as receiver.
        for module_name, module_info in self.gp.modules.iteritems():
            # We only need one instance to register ourselfs.
            instance = module_info['instances'][0]
            # Stand alone modules will be skipped.
            if instance.module_type == "stand_alone":
                continue
            if instance.module_type == "input":
                instance.addReceiver(self.__class__, TrackEvents.input_queue)
            # Register for on_event_delete.
            instance.registerCallback('on_event_delete', self.deleteEventFromRedis)

    def requeueEvents(self):
        # Check if events need to be requeued.
        input_modules = {}
        for module_name, module_info in self.gp.modules.iteritems():
            instance = module_info['instances'][0]
            if instance.module_type == "input":
                matches = re.search(self.class_name_re, str(instance.__class__))
                if matches:
                    input_modules[matches.group(1)] = instance
        keys = self.redis_client.keys("%s:*" % self.redis_key_prefix)
        if len(keys) > 0:
            self.logger.warning("%sFound %s unfinished events. Requeing...%s" % (Utils.AnsiColors.WARNING, len(keys), Utils.AnsiColors.ENDC))
            requeue_counter = 0
            for key in keys:
                event = self.getRedisValue(key)
                if event[0] not in input_modules:
                    self.logger.error("%sCould not requeue event. Module %s not found.%s" % (Utils.AnsiColors.WARNING, event[0], Utils.AnsiColors.ENDC))
                    continue
                requeue_counter += 1
                # Delete event from redis
                self.deleteEventFromRedis(event[1])
                input_modules[event[0]].receiveEvent(event[1])
            self.logger.warning("%sDone. Requeued %s of %s events.%s" % (Utils.AnsiColors.WARNING, requeue_counter, len(keys), Utils.AnsiColors.ENDC))

    def run(self):
        # Check if redis client is availiable.
        if not self.redisClientAvailiable():
            self.logger.error("%sThis module needs a redis client as backend but none could be found. Event tracking will be disabled!%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC))
            return
        # Only the main thread will execute configuration of running modules.
        if TrackEvents.main_thread == self:
            self.register()
            self.requeueEvents()
        # Call parent run method
        BaseThreadedModule.BaseThreadedModule.run(self)

    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        @return data: dictionary
        """
        #m = re.search(self.class_name_re, str(inspect.stack()[1][0].f_locals["self"].__class__))
        self.setRedisValue("%s:%s" % (self.redis_key_prefix, event['__id']), ('TcpServerTornado.TcpServerTornado', event), self.getConfigurationValue('redis_ttl'))
        yield event

    def deleteEventFromRedis(self, event):
        #print "Deleteing %s." % event
        self.redis_client.delete("%s:%s" % (self.redis_key_prefix, event['__id']))
