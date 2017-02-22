# -*- coding: utf-8 -*-
import socket
import sys
import urllib2

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser, setInterval
from lumbermill.utils.misc import TimedFunctionManager

@ModuleDocstringParser
class HttpRequest(BaseThreadedModule):
    """
    Issue an arbitrary http request and store the response in a configured field.

    If the <interval> value is set, this module will execute the configured request
    every <interval> seconds and emits the result in a new event.

    This module supports the storage of the responses in an redis db. If redis_store is set,
    it will first try to retrieve the response from redis via the key setting.
    If that fails, it will execute the http request and store the result in redis.

    url: The url to grab. Can also contain templated values for dynamic replacement with event data.
    socket_timeout: The socket timeout in seconds after which a request is considered failed.
    get_metadata: Also get metadata like headers, encoding etc.
    target_field: Specifies the name of the field to store the retrieved data in.
    interval: Number of seconds to wait before calling <url> again.
    redis_store: Redis address to cache crawling results.
    redis_key: The key to use for storage in redis.
    redis_ttl: TTL for data in redis.

    Configuration template:

    - HttpRequest:
       url:                             # <type: string; is: required>
       socket_timeout:                  # <default: 25; type: integer; is: optional>
       get_metadata:                    # <default: False; type: boolean; is: optional>
       target_field:                    # <default: "http_request_result"; type: string; is: optional>
       interval:                        # <default: None; type: None||float||integer; is: optional>
       redis_store:                     # <default: None; type: None||string; is: optional>
       redis_key:                       # <default: None; type: None||string; is: optional if redis_store is None else required>
       redis_ttl:                       # <default: 60; type: integer; is: optional>
       receivers:
        - NextModule
    """
    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        BaseThreadedModule.configure(self, configuration)
        socket.setdefaulttimeout(self.getConfigurationValue('socket_timeout'))
        self.get_metadata = self.getConfigurationValue('get_metadata')
        self.interval = self.getConfigurationValue('interval')
        # Get redis client module.
        if self.getConfigurationValue('redis_store'):
            mod_info = self.lumbermill.getModuleInfoById(self.getConfigurationValue('redis_store'))
            self.redis_store = mod_info['instances'][0]
        else:
            self.redis_store = None

    def getRunTimedFunctionsFunc(self):
        @setInterval(self.interval, call_on_init=True)
        def runTimedFunctionsFunc():
            event = DictUtils.getDefaultEventDict({}, caller_class_name="HttpRequest")
            self.receiveEvent(event)
        return runTimedFunctionsFunc

    def initAfterFork(self):
        if self.interval:
            TimedFunctionManager.startTimedFunction(self.getRunTimedFunctionsFunc())
        BaseThreadedModule.initAfterFork(self)

    def handleEvent(self, event):
        request_url = self.getConfigurationValue('url', event)
        target_field_name = self.getConfigurationValue('target_field', event)
        if not request_url or not target_field_name:
            yield event
            return
        response = None
        if self.redis_store:
            redis_key = self.getConfigurationValue('redis_key', event)
            response = self.redis_store.get(redis_key)
        if response is None:
            try:
                response = self.execRequest(request_url)
                # Copy data to a dict, since the response object can not be pickled to be stored in redis.
                response_dict = {'content': response.read(),
                                 'status_code': response.getcode(),
                                 'url': response.geturl()}
                if self.get_metadata:
                    response_dict.update({'headers': response.info().headers,
                                          'parameter_list': response.info().getplist(),
                                          'encoding': response.info().getencoding(),
                                          'type': response.info().gettype(),
                                          'maintype': response.info().getmaintype(),
                                          'subtype': response.info().getsubtype()})
                if response and self.redis_store:
                    self.redis_store.set(redis_key, response_dict, self.getConfigurationValue('redis_ttl'))
            except KeyError:
                yield event
                return
        event[target_field_name] = response_dict
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