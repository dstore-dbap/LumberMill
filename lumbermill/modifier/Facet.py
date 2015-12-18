# -*- coding: utf-8 -*-
import sys

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser, setInterval
from lumbermill.utils.misc import TimedFunctionManager


@ModuleDocstringParser
class Facet(BaseThreadedModule):
    """
    Collect different values of one field over a defined period of time and pass all
    encountered variations on as new event after period is expired.

    The "add_event_fields" configuration will copy the configured event fields into the "other_event_fields" list.

    The event emitted by this module will be of type: "facet" and will have "facet_field",
    "facet_count", "facets" and "other_event_fields" fields set.

    This module supports the storage of the facet info in an redis db. If redis_store is set,
    it will first try to retrieve the facet info from redis via the key setting.

    Configuration template:

    - Facet:
       source_field:                    # <type:string; is: required>
       group_by:                        # <type:string; is: required>
       add_event_fields:                # <default: []; type: list; is: optional>
       interval:                        # <default: 5; type: float||integer; is: optional>
       redis_store:                     # <default: None; type: None||string; is: optional>
       redis_ttl:                       # <default: 60; type: integer; is: optional>
       receivers:
        - NextModule
    """
    facet_data = {}
    """Holds the facet data for all instances"""

    redis_keys = []
    """Holds just the redis keys to all facet data"""

    module_type = "misc"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')
        self.add_event_fields = self.getConfigurationValue('add_event_fields')
        # Get redis client module.
        if self.getConfigurationValue('redis_store'):
            mod_info = self.lumbermill.getModuleInfoById(self.getConfigurationValue('redis_store'))
            self.redis_store = mod_info['instances'][0]
        else:
            self.redis_store = None

    def _getFacetInfoRedis(self, key):
        facet_info = self.redis_store.get(key)
        if not facet_info:
            facet_info = {'other_event_fields': {}, 'facets': []}
        return facet_info

    def _getFacetInfoInternal(self, key):
        try:
            facet_info = Facet.facet_data[key]
        except KeyError:
            facet_info = {'other_event_fields': {}, 'facets': []}
        return facet_info

    def getFacetInfo(self, key):
        if self.redis_store:
            return self._getFacetInfoRedis(key)
        return self._getFacetInfoInternal(key)

    def _setFacetInfoRedis(self, key, facet_info):
        try:
            self.redis_store.set(key, facet_info, self.getConfigurationValue('redis_ttl'))
            if key not in Facet.redis_keys:
                Facet.redis_keys.append(key)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not store facet data in redis. Exception: %s, Error: %s." % (etype, evalue))
            pass

    def _setFacetInfoInternal(self, key, facet_info):
        Facet.facet_data[key] = facet_info

    def setFacetInfo(self, key, facet_info):
        if self.redis_store:
            self._setFacetInfoRedis(key, facet_info)
            return
        self._setFacetInfoInternal(key, facet_info)

    def sendFacetEventToReceivers(self, facet_data):
        event = DictUtils.getDefaultEventDict({'facet_field': self.source_field,
                                          'facet_count': len(facet_data['facets']),
                                          'facets': facet_data['facets']},
                                          caller_class_name=self.__class__.__name__,
                                          event_type='facet')
        if facet_data['other_event_fields']:
            event['other_event_fields'] = facet_data['other_event_fields']
        self.sendEvent(event)

    def getEvaluateFunc(self):
        @setInterval(self.getConfigurationValue('interval'))
        def evaluateFacets():
            if self.redis_store:
                for key in Facet.redis_keys:
                    self.sendFacetEventToReceivers(self._getFacetInfoRedis(key))
                    # Clear redis items
                    self.redis_store.client.delete(key)
                Facet.redis_keys = []
                return
            # Just internal facet data.
            for key, facet_data in Facet.facet_data.items():
                self.sendFacetEventToReceivers(facet_data)
            Facet.facet_data = {}
        return evaluateFacets

    def initAfterFork(self):
        self.evaluate_facet_data_func = self.getEvaluateFunc()
        self.timed_func_handler = TimedFunctionManager.startTimedFunction(self.evaluate_facet_data_func)
        BaseThreadedModule.initAfterFork(self)

    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        @return data: dictionary
        """
        # Get key and value for facet from event.
        try:
            facet_value = event[self.getConfigurationValue('source_field', event)]
        except KeyError:
            yield event
            return
        key = self.getConfigurationValue('group_by', event)
        if not key and self.redis_store:
            self.logger.warning("Group_by value %s could not be generated. Event ignored." % (self.getConfigurationValue('group_by')))
            yield event
            return
        key = "FacetValues:%s" % key
        redis_lock = False
        try:
            # Acquire redis lock as well if configured to use redis store.
            if self.redis_store:
                redis_lock = self.redis_store.getLock("FacetLocks:%s" % key, timeout=1)
                if not redis_lock:
                    yield event
                    return
                redis_lock.acquire()
            facet_info = self.getFacetInfo(key)
            if facet_value not in facet_info['facets']:
                keep_fields = {}
                for field_name in self.add_event_fields:
                    try:
                        keep_fields[field_name] = event[field_name]
                    except KeyError:
                        pass
                if keep_fields:
                    facet_info['other_event_fields'][facet_value] = keep_fields
                facet_info['facets'].append(facet_value)
                self.setFacetInfo(key, facet_info)
        except:
            # Pass on all exceptions
            raise
        finally:
            # Make sure redis lock is released if we have one.
            if redis_lock:
                redis_lock.release()
        yield event

    def shutDown(self):
        # Push any remaining facet data.
        self.evaluate_facet_data_func(self)
        # Call parent configure method.
        BaseThreadedModule.shutDown(self)