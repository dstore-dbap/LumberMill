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
      configuration:
        redis_client: RedisClientName           # <type: string; is: required>
        queue_size: 5                           # <default: 5; type: integer; is: optional>
        redis_ttl: 3600                         # <default: 3600; type: integer; is: optional>
    """

    module_type = "misc"
    """Set module type"""

    can_run_parallel = True

    main_thread = False

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.redis_key_prefix = 'TrackEvents:%s' % socket.gethostname()
        if not TrackEvents.main_thread:
            TrackEvents.main_thread = self

    def register(self):
        # Get all input modules an register ourself as receiver.
        for module_name, module_info in self.gp.modules.iteritems():
            for instance in module_info['instances']:
                instance.registerCallback('on_event_delete', self.deleteEventFromRedis)

    def requeueEvents(self):
        # Check if events need to be requeued.
        input_modules = {}
        for module_name, module_info in self.gp.modules.iteritems():
            instance = module_info['instances'][0]
            if instance.module_type == "input":
                input_modules[instance.__class__.__name__] = instance
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
                input_modules[event[0]].sendEvent(event[1])
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
        event['gambolputty']['track_id'] = id(event)
        self.setRedisValue("%s:%s" % (self.redis_key_prefix, id(event)), (event['gambolputty']['source_module'], event), self.getConfigurationValue('redis_ttl'))
        yield event

    def deleteEventFromRedis(self, event):
        if 'track_id' in event['gambolputty']:
            self.redis_client.delete("%s:%s" % (self.redis_key_prefix, event['gambolputty']['track_id']))
