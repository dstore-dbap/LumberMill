# -*- coding: utf-8 -*-
import threading
import Utils
import BaseModule
import BaseThreadedModule
import Decorators
import sys

@Decorators.ModuleDocstringParser
class Facet(BaseModule.BaseModule):
    """
    Collect different values of one field over a defined period of time and pass all
    encountered variations on as new event after period is expired.

    The "add_event_fields" configuration will copy the configured event fields into the "other_event_fields" list.

    The event emitted by this module will be of type: "facet" and will have "facet_field",
    "facet_count", "facets" and "other_event_fields" fields set.

    This module supports the storage of the facet info in an redis db. If redis-client is set,
    it will first try to retrieve the facet info from redis via the key setting.

    Configuration example:

    - module: Facet
      configuration:
        source_field: url                       # <type:string; is: required>
        group_by: %(remote_ip)s                 # <type:string; is: required>
        add_event_fields: [user_agent]          # <default: []; type: list; is: optional>
        interval: 30                            # <default: 5; type: float||integer; is: optional>
        redis_client: RedisClientName           # <default: ""; type: string; is: optional>
        redis_ttl: 600                          # <default: 60; type: integer; is: optional>
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
        BaseModule.BaseModule.configure(self, configuration)
        self.evaluate_facet_data_func = self.getEvaluateFunc()
        self.evaluate_facet_data_func(self)
        self.lock = threading.Lock()

    def _getFacetInfoRedis(self, key):
        facet_info = self.getRedisValue(key)
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
        if self.redisClientAvailiable():
            return self._getFacetInfoRedis(key)
        return self._getFacetInfoInternal(key)

    def _setFacetInfoRedis(self, key, facet_info):
        try:
            self.setRedisValue(key, facet_info, self.getConfigurationValue('redis_ttl'))
            if key not in Facet.redis_keys:
                Facet.redis_keys.append(key)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("%sCould not store facet data in redis.%s" % (Utils.AnsiColors.WARNING, key, etype, evalue, Utils.AnsiColors.WARNING))
            pass

    def _setFacetInfoInternal(self, key, facet_info):
        Facet.facet_data[key] = facet_info

    def setFacetInfo(self, key, facet_info):
        if self.redisClientAvailiable():
            self._setFacetInfoRedis(key, facet_info)
            return
        self._setFacetInfoInternal(key, facet_info)

    def sendFacetEventToReceivers(self, facet_data):
        event = Utils.getDefaultEventDict({'event_type': 'facet',
                                          'facet_field': self.getConfigurationValue('source_field'),
                                          'facet_count': len(facet_data['facets']),
                                          'facets': facet_data['facets'],
                                          'other_event_fields': facet_data['other_event_fields']})
        self.sendEvent(event)

    def getEvaluateFunc(self):
        @Decorators.setInterval(self.getConfigurationValue('interval'))
        def evaluateFacets(self):
            if self.redisClientAvailiable():
                for key in Facet.redis_keys:
                    self.sendFacetEventToReceivers(self._getFacetInfoRedis(key))
                    # Clear redis items
                    self.redis_client.delete(key)
                Facet.redis_keys = []
                return
            # Just internal facet data.
            for key, facet_data in Facet.facet_data.iteritems():
                self.sendFacetEventToReceivers(facet_data)
            Facet.facet_data = {}
        return evaluateFacets

    def shutDown(self):
        # Push any remaining facet data.
        self.evaluate_facet_data_func(self)
        # Call parent configure method.
        BaseModule.BaseModule.shutDown(self)

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
        with self.lock:
            redis_lock = False
            try:
                # Acquire redis lock as well if configured to use redis store.
                redis_lock = self.getRedisLock("FacetLocks:%s" % key, timeout=1)
                if redis_lock:
                    redis_lock.acquire()
                facet_info = self.getFacetInfo(key)
                if facet_value not in facet_info['facets']:
                    keep = {}
                    for keep_field in self.getConfigurationValue('add_event_fields'):
                        try:
                            keep[keep_field] = event[keep_field]
                        except KeyError:
                            pass
                    facet_info['other_event_fields'][facet_value] = keep
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