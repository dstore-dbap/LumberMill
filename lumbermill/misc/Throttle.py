# -*- coding: utf-8 -*-
from collections import defaultdict
import time

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser, setInterval


@ModuleDocstringParser
class Throttle(BaseThreadedModule):
    """
    Throttle event count over a given time period.

    key: Identifies events as being the "same". Dynamic notations can be used here.
    timeframe: Time window in seconds from first encountered event to last.
    min_count: Minimal count of same events to allow event to be passed on.
    max_mount: Maximum count of same events before same events will be blocked.
    backend: Name of a key::value store plugin. When running multiple instances of gp this backend can be used to synchronize events across multiple instances.
    backend_key_prefix: Prefix for the backend key.

    Configuration template:

    - Throttle:
       key:                             # <type:string; is: required>
       timeframe:                       # <default: 600; type: integer; is: optional>
       min_count:                       # <default: 1; type: integer; is: optional>
       max_count:                       # <default: 1; type: integer; is: optional>
       backend:                         # <default: None; type: None||string; is: optional>
       backend_key_prefix:              # <default: "lumbermill:throttle"; type: string; is: optional>
       receivers:
        - NextModule
    """

    module_type = "misc"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.throttled_events_info = defaultdict(int)
        self.key = self.getConfigurationValue('key')
        self.timeframe = self.getConfigurationValue('timeframe')
        self.min_count = self.getConfigurationValue('min_count')
        self.max_count = self.getConfigurationValue('max_count')
        self.backend_key_prefix = self.getConfigurationValue('backend_key_prefix')
        self.persistence_backend = None
        if self.getConfigurationValue('backend'):
            backend_info = self.lumbermill.getModuleInfoById(self.getConfigurationValue('backend'))
            if not backend_info:
                self.logger.error("Could not find %s backend for persistant storage." % (self.getConfigurationValue('backend')))
                self.lumbermill.shutDown()
                return
            self.persistence_backend = backend_info['instances'][0]

    def setAndGetEventCountByKey(self, key):
        now = time.time()
        if self.persistence_backend:
            throttled_event_info = self.persistence_backend.get("%s:%s" % (self.backend_key_prefix, key))
        else:
            try:
                throttled_event_info = self.throttled_events_info[key]
            except KeyError:
                throttled_event_info  = None
        if not throttled_event_info or (now - throttled_event_info['ctime']) > self.timeframe:
            throttled_event_info = {'count': 1, 'ctime': now}
        else:
            throttled_event_info['count'] += 1
        if self.persistence_backend:
            self.persistence_backend.set("%s:%s" % (self.backend_key_prefix, key), throttled_event_info)
        else:
            self.throttled_events_info[key] = throttled_event_info
        return throttled_event_info['count']

    def getGcThrottledEventsInfoFunc(self):
        @setInterval(15)
        def gcThrottledEventsInfo():
            now = time.time()
            if self.persistence_backend:
                throttled_event_keys = self.persistence_backend.client.keys("%s:*" % self.backend_key_prefix)
                if not throttled_event_keys:
                    return
                keys_to_delete = []
                for key in throttled_event_keys:
                    throttled_event_info = self.persistence_backend.get(key)
                    if (now - throttled_event_info['ctime']) > self.timeframe:
                        keys_to_delete.append(key)
                if keys_to_delete:
                    self.persistence_backend.client.delete(*keys_to_delete)
                return
            throttled_events_info_copy = self.throttled_events_info.copy()
            for key, throttled_event_info in throttled_events_info_copy.items():
                if (now - throttled_event_info['ctime']) > self.timeframe:
                    del self.throttled_events_info[key]
        return gcThrottledEventsInfo

    def initAfterFork(self):
        self.gc_throttled_events_info = self.getGcThrottledEventsInfoFunc()
        self.timed_func_handler = Utils.TimedFunctionManager.startTimedFunction(self.gc_throttled_events_info)
        BaseThreadedModule.initAfterFork(self)

    def handleEvent(self, event):
        throttled_event_key = Utils.mapDynamicValue(self.key, event)
        throttled_event_count = self.setAndGetEventCountByKey(throttled_event_key)
        if self.min_count <= throttled_event_count <= self.max_count:
            yield event