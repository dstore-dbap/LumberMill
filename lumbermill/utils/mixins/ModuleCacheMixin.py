# -*- coding: utf-8 -*-


class ModuleCacheMixin:

    def _getFromCache(self, cache_key, event):
        try:
            result = self.cache.get(cache_key)
            event['lumbermill']['cache_hit'] = True
        except KeyError:
            event['lumbermill']['cache_hit'] = False
            result = None
        return result

    def configure(self):
        self.cache = self.getConfigurationValue('cache')
        if not self.cache:
            return
        mod_info = self.lumbermill.getModuleInfoById(self.cache)
        if not mod_info:
            self.logger.error("Could not find cache module: %s." % self.cache)
            self.lumbermill.shutDown()
            return
        self.cache = mod_info['instances'][0]
        self.cache_lock = None
        self.cache_key_name = self.getConfigurationValue('cache_key')
        self.cache_lock_name = self.getConfigurationValue('cache_lock')
        self.cache_ttl = self.getConfigurationValue('cache_ttl')
        # We need a lock if multiple processes work on the same data.
        if self.cache_lock_name and self.lumbermill.getWorkerCount() > 1:
            self.cache_lock = self.cache.getLock(self.cache_lock_name, timeout=10)
            if not self.cache_lock:
                self.logger.error("Could not acquire cache lock. Please check module configuration for module %s." % (self.getConfigurationValue('cache')))
                self.lumbermill.shutDown()
                return
