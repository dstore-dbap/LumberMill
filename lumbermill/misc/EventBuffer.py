# -*- coding: utf-8 -*-
import copy
import gc
import random
import sys

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser, setInterval

@ModuleDocstringParser
class EventBuffer(BaseThreadedModule):
    """
    Store received events in a persistent backend until the event was successfully handled.
    Events, that did not get handled correctly, will be requeued when LumberMill is restarted.

    At the moment only RedisStore is supported as backend.

    As a technical note: This module is based on pythons garbage collection. If an event is
    created, a copy of the event is stored in the persistence backend. If it gets garbage collected,
    the event will be deleted from the backend.
    When used, this module forces a garbage collection every <gc_interval> seconds.
    This approach seemed to be the fastest and simplest with a small drawback:
    IMPORTANT: It is not absolutely guaranteed, that an event will be collected, thus the event will
    not be deleted from the backend data. This can cause a limited amount of duplicate events being
    send to the sinks.
    With an elasticsearch sink, this should be no problem, as long as your document id
    stays the same for the same event data. This is also true for the default event_id.

    Configuration template:

    - EventBuffer:
       backend:                         # <default: 'RedisStore'; type: string; is: optional>
       gc_interval:                     # <default: 5; type: integer; is: optional>
       key_prefix:                      # <default: "lumbermill:eventbuffer"; type: string; is: optional>
       """

    module_type = "stand_alone"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.key_prefix = self.getConfigurationValue('key_prefix')
        self.key_buffer = {}
        self.flush_interval = self.getConfigurationValue('gc_interval')
        self.requeue_events_done = False
        backend_info = self.lumbermill.getModuleInfoById(self.getConfigurationValue('backend'))
        if not backend_info:
            self.logger.error("Could not find %s backend for persistant storage." % (self.getConfigurationValue('backend')))
            self.lumbermill.shutDown()
            return
        self.persistence_backend = backend_info['instances'][0]
        Utils.KeyDotNotationDict.persistence_backend = self.persistence_backend
        Utils.KeyDotNotationDict.key_prefix = self.key_prefix
        # Monkeypatch Utils.KeyDotNotationDict to add/delete event to persistence backend.
        def removeFromPersistenceBackendOnGarbageCollect(self):
            Utils.KeyDotNotationDict.___del___(self)
            # Only act if we hold an event.
            if "event_id" not in self.get("lumbermill", {}):
                return
            #print "Removing from backend"
            try:
                key = "%s:%s" % (Utils.KeyDotNotationDict.key_prefix, self['lumbermill']['event_id'])
                Utils.KeyDotNotationDict.persistence_backend.delete(key)
            except:
                pass
        Utils.KeyDotNotationDict.___del___ = Utils.KeyDotNotationDict.__del__
        Utils.KeyDotNotationDict.__del__ = removeFromPersistenceBackendOnGarbageCollect

        def addToPersistenceBackendOnInit(self, *args):
            Utils.KeyDotNotationDict.___init___(self, *args)
            # Only act if we hold an event.
            if "event_id" not in self.get("lumbermill", {}):
                return
            try:
                key = "%s:%s" % (Utils.KeyDotNotationDict.key_prefix, self['lumbermill']['event_id'])
                # Store a simple dict in backend, not a KeyDotNotationDict.
                # Also, store a copy, as the dict might get buffered in persistence_backend and we do not
                # want any changes made to new_dict to propagate to persistence_backend.
                Utils.KeyDotNotationDict.persistence_backend.set(key, dict.copy(self), False)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not store event in persistance backend. Exception: %s, Error: %s." % (etype, evalue))
                pass
            print "Added to backend"
        Utils.KeyDotNotationDict.___init___ = Utils.KeyDotNotationDict.__init__
        Utils.KeyDotNotationDict.__init__ = addToPersistenceBackendOnInit

        def returnSimpleKeyDotDictOnCopy(self):
            """
            When creating a copy of an event, we do not want to store/remove this in/from the persistence backend.
            When the original event is requeued it will pass through all modules again, thus creating the
            same copies etc.
            A removeFromPersistenceBackendOnGarbageCollect would fail anyways, since the new key is unknown to the
            backend. Still we can skip removing for speedups.
            """
            new_dict = Utils.KeyDotNotationDict()
            new_dict.__init__ = Utils.KeyDotNotationDict.___init___
            new_dict.__del__ = Utils.KeyDotNotationDict.__del__
            new_dict.update(copy.deepcopy(super(Utils.KeyDotNotationDict, self)))
            if "event_id" in new_dict.get("lumbermill", {}):
                new_dict['lumbermill']['event_id'] = "%032x" % random.getrandbits(128)
            return new_dict
        Utils.KeyDotNotationDict.copy = returnSimpleKeyDotDictOnCopy

    def getTimedGarbageCollectFunc(self):
        @setInterval(self.flush_interval, call_on_init=True)
        def timedGarbageCollect():
            if not self.requeue_events_done:
                self.requeueEvents()
                self.requeue_events_done = True
            gc.collect()
        return timedGarbageCollect

    def requeueEvents(self):
        input_modules = {}
        for module_name, module_info in self.lumbermill.modules.items():
            instance = module_info['instances'][0]
            if instance.module_type == "input":
                input_modules[instance.__class__.__name__] = instance
        for key in self.persistence_backend.iterKeys():
            if not key.startswith("%s" % self.key_prefix):
                continue
            self.logger.warning("Found %s unfinished events. Requeing..." % (len(keys)))
            requeue_counter = 0
            for key in keys:
                event = self.persistence_backend.pop(key)
                if not event:
                    continue
                if "source_module" not in event.get("lumbermill", {}):
                    self.logger.warning("Could not requeue event. Source module info not found in event data.")
                    continue
                source_module = event["lumbermill"]["source_module"]
                if source_module not in input_modules:
                    self.logger.error("Could not requeue event. Module %s not found." % (source_module))
                    continue
                requeue_counter += 1
                input_modules[source_module].sendEvent(Utils.KeyDotNotationDict(event))
            self.logger.warning("Done. Requeued %s of %s events." % (requeue_counter, len(keys)))
            self.logger.warning("Note: If more than one gp instance is running, requeued events count may differ from total events.")
            event = None

    def start(self):
        self.timedFuncHandle = Utils.TimedFunctionManager.startTimedFunction(self.getTimedGarbageCollectFunc())