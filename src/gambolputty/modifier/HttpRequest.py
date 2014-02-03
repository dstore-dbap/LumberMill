# -*- coding: utf-8 -*-
import sys
import urllib2
import socket
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class HttpRequest(BaseThreadedModule.BaseThreadedModule):
    """
    Issue an arbitrary http request and store the response in a configured field.

    This module supports the storage of the responses in an redis db. If redis-client is set,
    it will first try to retrieve the respone from redis via the key setting.
    If that fails, it will execute the http request and store the result in redis.

    Configuration example:

    - module: HttpRequest
      url:                                    # <type: string; is: required>
      socket_timeout:                         # <default: 25; type: integer; is: optional>
      target_field:                           # <default: "gambolputty_http_request"; type: string; is: optional>
      redis_store:                            # <default: None; type: None||string; is: optional>
      redis_key:                              # <default: None; type: None||string; is: optional if redis_store is None else required>
      redis_ttl:                              # <default: 60; type: integer; is: optional>
      receivers:
        - NextModule
    """
    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        socket.setdefaulttimeout(self.getConfigurationValue('socket_timeout'))
        # Get redis client module.
        if self.getConfigurationValue('redis_store'):
            mod_info = self.gp.getModuleInfoById(self.getConfigurationValue('redis_store'))
            self.redis_store = mod_info['instances'][0]
        else:
            self.redis_store = None

    def handleEvent(self, event):
        if 'TreeNodeID' not in event:
            yield event
            return
        try:
            is_int = int(event['TreeNodeID'])
        except:
            yield event
            return
        request_url = self.getConfigurationValue('url', event)
        target_field_name = self.getConfigurationValue('target_field', event)
        if not request_url or not target_field_name:
            yield event
            return
        result = None
        if self.redis_store:
            result = self.redis_store.getValue(self.getConfigurationValue('redis_key', event))
        if result == None:
            try:
                result = self.execRequest(request_url).read()
                if result and self.redis_store:
                    self.redis_store.setValue(self.getConfigurationValue('redis_key', event), result, self.getConfigurationValue('redis_ttl'))
            except:
                yield event
                return
        event[target_field_name] =  result
        yield event

    def execRequest(self, url):
        try:
            response = urllib2.urlopen(url)
            return response
        except urllib2.HTTPError, e:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Request to %s failed. Exception: %s, Error: %s" % (url, etype, evalue))
            raise
        except urllib2.URLError, e:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Request to %s failed. Exception: %s, Error: %s" % (url, etype, evalue))
            raise
        return False