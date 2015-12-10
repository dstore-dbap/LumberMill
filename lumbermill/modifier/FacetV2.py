# -*- coding: utf-8 -*-
import sys

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser, setInterval


@ModuleDocstringParser
class FacetV2(BaseThreadedModule):
    """
    Collect different values of one field over a defined period of time and pass all
    encountered variations on as new event after period is expired.

    The "add_event_fields" configuration will copy the configured event fields into the "other_event_fields" list.

    The event emitted by this module will be of type: "facet" and will have "facet_field",
    "facet_count", "facets" and "other_event_fields" fields set.

    This module supports the storage of the facet info in an backend db (At the moment this only works for a redis backend.
    This offers the possibility of using this module across multiple instances of LumberMill.

    source_field: Field to be scanned for unique values.
    group_by: Field to relate the variations to, e.g. ip address.
    add_event_fields: Fields to add from the original event to the facet event.
    interval: Number of seconds to until all encountered values of source_field will be send as new facet event.
    backend: Name of a key::value store plugin. When running multiple instances of gp this backend can be used to
             synchronize events across multiple instances.
    backend_ttl: Time to live for backend entries. Should be greater than interval.

    Configuration template:

    - Facet:
       source_field:                    # <type:string; is: required>
       group_by:                        # <type:string; is: required>
       add_event_fields:                # <default: []; type: list; is: optional>
       interval:                        # <default: 5; type: float||integer; is: optional>
       backend:                         # <default: None; type: None||string; is: optional>
       backend_ttl:                     # <default: 60; type: integer; is: optional>
       receivers:
        - NextModule
    """
    facet_data = {}
    """Holds the facet data for all instances"""

    backend_keys = []
    """Holds just the backend keys to all facet data"""

    module_type = "misc"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')
        self.group_by_field = self.getConfigurationValue('group_by')
        self.add_event_fields = self.getConfigurationValue('add_event_fields')
        self.backend_ttl = self.getConfigurationValue('backend_ttl')
        self.persistence_backend = None
        if self.getConfigurationValue('backend'):
            backend_info = self.lumbermill.getModuleInfoById(self.getConfigurationValue('backend'))
            if not backend_info:
                self.logger.error("Could not find %s backend for persistant storage." % (self.getConfigurationValue('backend')))
                self.lumbermill.shutDown()
                return
            self.persistence_backend = backend_info['instances'][0]

    def getFacetDataFromRedis(self, key):
        facet_info = self.persistence_backend.get(key)
        if not facet_info:
            facet_info = False
        return facet_info

    def getFacetDataInternal(self, key):
        try:
            facet_info = FacetV2.facet_data[key]
        except KeyError:
            facet_info = False
        return facet_info

    def getFacetData(self, key):
        facet_data = self.getFacetDataInternal(key)
        if not facet_data and self.persistence_backend:
            facet_data = self.getFacetDataFromRedis(key)
        if not facet_data:
            facet_data = {'other_event_fields': {}, 'facets': []}
        return facet_data

    def setFacetDataInRedis(self, key, facet_data):
        try:
            self.persistence_backend.set(key, facet_data, self.backend_ttl)
            if key not in FacetV2.backend_keys:
                FacetV2.backend_keys.append(key)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not store facet data in persistance backend. Exception: %s, Error: %s." % (etype, evalue))
            pass

    def setFacetData(self, key, facet_info):
        FacetV2.facet_data[key] = facet_info

    def sendFacetEventToReceivers(self, facet_data):
        event = Utils.getDefaultEventDict({'facet_field': self.source_field,
                                          'facet_count': len(facet_data['facets']),
                                          'facets': facet_data['facets']},
                                          caller_class_name=self.__class__.__name__,
                                          event_type='facet')
        if facet_data['other_event_fields']:
            event['other_event_fields'] = facet_data['other_event_fields']
        self.sendEvent(event)

    def evaluateFacets(self):
        """
        This is a method on its on and not implemented in timedEvaluateFacets because the shutDown method needs to call
        this as well and it needs to be executed directly.
        """
        if self.persistence_backend:
            backend_lock = self.persistence_backend.getLock("FacetLock", timeout=10)
            if not backend_lock:
                return
            lock_acquired = backend_lock.acquire(blocking=True)
            if not lock_acquired:
                return
            for key in FacetV2.backend_keys:
                facet_data = self.getFacetDataFromRedis(key)
                if facet_data:
                    self.sendFacetEventToReceivers(facet_data)
                # Clear backend items
                self.persistence_backend.client.delete(key)
            FacetV2.backend_keys = []
            backend_lock.release()
            return
        # Just internal facet data.
        for key, facet_data in FacetV2.facet_data.items():
            self.sendFacetEventToReceivers(facet_data)
        FacetV2.facet_data = {}

    def getEvaluateFunc(self):
        @setInterval(self.getConfigurationValue('interval'))
        def timedEvaluateFacets():
            self.evaluateFacets()
        return timedEvaluateFacets

    def getStoreFunc(self):
        @setInterval(1)
        def storeFacetsInRedis():
            backend_lock = self.persistence_backend.getLock("FacetLock", timeout=10)
            if not backend_lock:
                return
            lock_acquired = backend_lock.acquire(blocking=True)
            if not lock_acquired:
                return
            for key, facet_data in FacetV2.facet_data.items():
                current_facet_data = self.getFacetDataFromRedis(key)
                if not current_facet_data:
                    current_facet_data = {'other_event_fields': {}, 'facets': []}
                if 'other_event_fields' in current_facet_data:
                    current_facet_data['other_event_fields'].update(facet_data['other_event_fields'])
                current_facet_data['facets'] += facet_data['facets']
                self.setFacetDataInRedis(key, current_facet_data)
            FacetV2.facet_data = {}
            backend_lock.release()
        return storeFacetsInRedis


    def initAfterFork(self):
        self.evaluate_facet_data_func = self.getEvaluateFunc()
        self.timed_func_handler_a = Utils.TimedFunctionManager.startTimedFunction(self.evaluate_facet_data_func)
        if self.persistence_backend:
            self.store_facets_in_backend_func = self.getStoreFunc()
            self.timed_func_handler_b = Utils.TimedFunctionManager.startTimedFunction(self.store_facets_in_backend_func)
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
        key = event[self.group_by_field]
        if not key and self.persistence_backend:
            self.logger.warning("Group_by value %s could not be generated. Event ignored." % (self.getConfigurationValue('group_by')))
            yield event
            return
        key = "FacetValues:%s" % key
        facet_data = self.getFacetData(key)
        if facet_value not in facet_data['facets']:
            keep_fields = {}
            for field_name in self.add_event_fields:
                try:
                    keep_fields[field_name] = event[field_name]
                except KeyError:
                    pass
            if keep_fields:
                facet_data['other_event_fields'][facet_value] = keep_fields
            facet_data['facets'].append(facet_value)
            self.setFacetData(key, facet_data)
        yield event

    def shutDown(self):
        # Push any remaining facet data.
        self.evaluateFacets()
        # Call parent configure method.
        BaseThreadedModule.shutDown(self)