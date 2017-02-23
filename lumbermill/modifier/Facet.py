# -*- coding: utf-8 -*-
import sys
import hashlib

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.mixins.ModuleCacheMixin import ModuleCacheMixin
from lumbermill.utils.Decorators import ModuleDocstringParser, setInterval
from lumbermill.utils.misc import TimedFunctionManager


@ModuleDocstringParser
class Facet(BaseThreadedModule, ModuleCacheMixin):
    """
    Collect different values of one field over a defined period of time and pass all
    encountered variations on as new event after period is expired.

    The "add_event_fields" configuration will copy the configured event fields into the "other_event_fields" list.

    The event emitted by this module will be of type: "facet" and will have "facet_field",
    "facet_count", "facets" and "other_event_fields" fields set.

    This module uses the cache module to store the facet info.
    This offers the possibility of using this module across multiple instances of LumberMill and also solves problems
    when running LumberMill with multiple processes.

    source_field: Field to be scanned for unique values.
    group_by: Field to relate the variations to, e.g. ip address.
    cache: Name of the cache plugin. When running multiple instances of lumbermill this cache can be used to
           synchronize events across multiple instances.
    cache_key: Keyname to use to store the facet data in cache.
    cache_lock: Lockname to use if multiple instances of Lumbermill work on the same data.
    cache_ttl: Time to live for cached entries. Should be greater than interval.
    add_event_fields: Fields to add from the original event to the facet event.
    interval: Number of seconds to until all encountered values of source_field will be send as new facet event.

    Configuration template:

    - Facet:
       source_field:                    # <type:string; is: required>
       group_by:                        # <type:string; is: required>
       cache:                           # <default: 'Cache'; type: string; is: required>
       cache_key:                       # <default: 'Lumbermill:Facet:FacetKeyCache'; type: string; is: required>
       cache_lock:                      # <default: 'Lumbermill:Facet:FacetLock'; type: string; is: required>
       cache_ttl:                       # <default: 60; type: integer; is: optional>
       add_event_fields:                # <default: []; type: list; is: optional>
       interval:                        # <default: 5; type: float||integer; is: optional>
       receivers:
        - NextModule
    """
    facet_data = {}
    """Holds the facet data for all instances"""

    module_type = "misc"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        ModuleCacheMixin.configure(self)
        self.source_field = self.getConfigurationValue('source_field')
        self.add_event_fields = self.getConfigurationValue('add_event_fields')

    def setFacetDataInCache(self, key, facet_data):
        try:
            self.cache.set(key, facet_data, self.cache_ttl)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not store facet data in persistance cache. Exception: %s, Error: %s." % (etype, evalue))
            pass

    def sendFacetEventToReceivers(self, facet_data):
        event = DictUtils.getDefaultEventDict({'facet_field': self.source_field,
                                          'facet_count': len(facet_data['facets']),
                                          'facets': facet_data['facets']},
                                          caller_class_name=self.__class__.__name__,
                                          event_type='facet')
        event['other_event_fields'] = facet_data['other_event_fields']
        self.sendEvent(event)

    def evaluateFacets(self):
        """
        This is a method on its on and not implemented in timedEvaluateFacets because the shutDown method needs to call
        this as well and it needs to be executed directly.
        """
        self.storeFacetsInCache()
        if self.cache_lock:
            lock_acquired = self.cache_lock.acquire(blocking=True)
            if not lock_acquired:
                return
        try:
            cache_facet_keys = self.cache.get(self.cache_key_name)
        except KeyError:
            cache_facet_keys = None
            pass
        if cache_facet_keys:
            for key in cache_facet_keys:
                facet_data = self.cache.get(key)
                if not facet_data:
                    continue
                self.sendFacetEventToReceivers(facet_data)
                self.cache.delete(key)
        self.cache.delete(self.cache_key_name)
        if self.cache_lock:
            try:
                self.cache_lock.release()
            except:
                etype, evalue, etb = sys.exc_info()
                if str(evalue) == "Cannot release a lock that's no longer owned":
                    pass
                else:
                    raise

    def storeFacetsInCache(self):
        if not Facet.facet_data:
            return
        if self.cache_lock:
            lock_acquired = self.cache_lock.acquire(blocking=True)
            if not lock_acquired:
                return
        update_cache_facet_keys = False
        try:
            cache_facet_keys = self.cache.get(self.cache_key_name)
        except KeyError:
            cache_facet_keys = []
        for key, facet_data in Facet.facet_data.items():
            current_facet_data = None
            if key in cache_facet_keys:
                current_facet_data = self.cache.get(key)
            else:
                update_cache_facet_keys = True
                cache_facet_keys.append(key)
            if not current_facet_data:
                current_facet_data = {'other_event_fields': [], 'facets': []}
            current_facet_data['other_event_fields'].extend(facet_data['other_event_fields'])
            for facet_value in facet_data['facets']:
                if facet_value in current_facet_data['facets']:
                    continue
                current_facet_data['facets'].append(facet_value)
            self.setFacetDataInCache(key, current_facet_data)
        if update_cache_facet_keys:
            self.setFacetDataInCache(self.cache_key_name, cache_facet_keys)
        Facet.facet_data = {}
        if self.cache_lock:
            try:
                self.cache_lock.release()
            except:
                etype, evalue, etb = sys.exc_info()
                if str(evalue) == "Cannot release a lock that's no longer owned":
                    pass
                else:
                    raise

    def initAfterFork(self):
        self.evaluate_facet_data_func = setInterval(self.getConfigurationValue('interval'))(self.evaluateFacets) #self.getEvaluateFunc()
        self.timed_func_handler_a = TimedFunctionManager.startTimedFunction(self.evaluate_facet_data_func)
        if self.cache:
            self.store_facets_in_cache_func = setInterval(1)(self.storeFacetsInCache)
            self.timed_func_handler_b = TimedFunctionManager.startTimedFunction(self.store_facets_in_cache_func)
        BaseThreadedModule.initAfterFork(self)

    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        @return data: dictionary
        """
        # Get key and value for facet from event.
        try:
            facet_value = event[self.source_field]
        except KeyError:
            yield event
            return
        key = hashlib.md5(self.getConfigurationValue('group_by', event)).hexdigest()
        if not key:
            self.logger.warning("Group_by value %s could not be generated. Event ignored." % (self.getConfigurationValue('group_by')))
            yield event
            return
        if self.cache.getBackendName() == 'RedisStore':
            # Redis uses : as tree separator.
            key = "%s:%s" % (self.cache_key_name, key)
        else:
            key = "%s_%s" % (self.cache_key_name, key)
        if key not in Facet.facet_data or facet_value not in Facet.facet_data[key]['facets']:
            if key in Facet.facet_data:
                facet_data = Facet.facet_data[key]
            else:
                facet_data = {'other_event_fields': [], 'facets': []}
            keep_fields = {}
            for field_name in self.add_event_fields:
                try:
                    keep_fields[field_name] = event[field_name]
                except KeyError:
                    pass
            if keep_fields:
                keep_fields['facet'] = str(facet_value)
                try:
                    facet_data['other_event_fields'].append(keep_fields)
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("Exception: %s, Error: %s." % (etype, evalue))
            facet_data['facets'].append(facet_value)
            Facet.facet_data[key] = facet_data
        yield event

    def shutDown(self):
        # Push any remaining facet data.
        self.evaluateFacets()
        # Call parent configure method.
        BaseThreadedModule.shutDown(self)