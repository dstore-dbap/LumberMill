# -*- coding: utf-8 -*-
import Utils
import BaseModule
import BaseThreadedModule
import Decorators

@Decorators.ModuleDocstringParser
class Facet(BaseThreadedModule.BaseThreadedModule):
    """
    Collect different values of one field over a defined period of time and pass all
    encountered variations on as new event after period is expired.

    The event emitted by this module will be of type: "facet" and will have "facet_field",
    "facet_count", "facets" and "factets_context_data" fields set.

    This module supports the storage of the facet info in an redis db. If redis-client is set,
    it will first try to retrieve the facet info from redis via the key setting.

    Configuration example:

    - module: Facet
      configuration:
        source_field: url                       # <type:string; is: required>
        group_by: %(remote_ip)s                 # <type:string; is: required>
        keep_fields: [user_agent]               # <default: []; type: list; is: optional>
        interval: 30                            # <default: 5; type: float||integer; is: optional>
        redis_client: RedisClientName           # <default: ""; type: string; is: optional>
        redis_ttl: 600                          # <default: 60; type: integer; is: optional>
      receivers:
        - NextModule
    """
    facet_data = {}
    """Holds the facet data for all instances"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.evaluate_facet_data_func = self.getEvaluateFunc()
        self.evaluate_facet_data_func(self)

    def getFacetInfo(self, key):
        # Try redis first.
        facet_info = self.getRedisValue(key)
        if not facet_info:
            # Try internal dictionary.
            try:
                facet_info = Facet.facet_data[key]
            except KeyError:
                facet_info = Facet.facet_data[key] = {'context_data': [], 'facets': []}
        return facet_info

    def setFacetInfo(self, key, facet_info):
        # Try redis first.
        stored = self.setRedisValue(key, facet_info, self.getConfigurationValue('redis_ttl'))
        if stored:
            # Update internal dict with just the facet key.
            Facet.facet_data[key] = 'Redis'
            return
        # Use internal dictionary
        Facet.facet_data[key] = facet_info

    def getEvaluateFunc(self):
        @Decorators.setInterval(self.getConfigurationValue('interval'))
        def evaluateFacets(self):
            if not Facet.facet_data:
              return
            for key, facet_data in Facet.facet_data.iteritems():
                if facet_data == 'Redis':
                    facet_data = self.getFacetInfo(key)
                    # Clear redis items
                    self.redis_client.delete(key)
                event = Utils.getDefaultDataDict({'event_type': 'facet',
                                                  'facet_field': self.getConfigurationValue('source_field'),
                                                  'facet_count': len(facet_data['facets']),
                                                  'facets': facet_data['facets'],
                                                  'facets_context_data': facet_data['context_data']})
                self.addEventToOutputQueues(event)
            Facet.facet_data = {}
        return evaluateFacets

    def shutDown(self):
        # Call parent configure method.
        BaseThreadedModule.BaseThreadedModule.shutDown(self)
        # Push any remaining facet data.
        self.evaluate_facet_data_func(self)

    def handleData(self, event):
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
        with BaseModule.BaseModule.lock:
            redis_lock = False
            try:
                # Acquire redis lock as well if configured to use redis store.
                redis_lock = self.getRedisLock("FacetLocks:%s" % key, timeout=1)
                if redis_lock:
                    redis_lock.acquire()
                facet_info = self.getFacetInfo(key)
                if facet_value not in facet_info['facets']:
                    keep = {}
                    for keep_field in self.getConfigurationValue('keep_fields'):
                        try:
                            keep[keep_field] = event[keep_field]
                        except KeyError:
                            pass
                    facet_info['context_data'].append(keep)
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