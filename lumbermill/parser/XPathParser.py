# -*- coding: utf-8 -*-
import sys

from lxml import etree

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class XPathParser(BaseThreadedModule):
    """
    Parse an xml string via xpath.

    This module supports the storage of the results in an redis db. If redis-client is set,
    it will first try to retrieve the result from redis via the key setting.
    If that fails, it will execute the xpath query and store the result in redis.

    Configuration template:

    - XPathParser:
       source_field:                    # <type: string; is: required>
       target_field:                    # <default: "gambolputty_xpath"; type: string; is: optional>
       query:                           # <type: string; is: required>
       redis_store:                     # <default: None; type: None||string; is: optional>
       redis_key:                       # <default: None; type: None||string; is: optional if redis_store is None else required>
       redis_ttl:                       # <default: 60; type: integer; is: optional>
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        BaseThreadedModule.configure(self, configuration)
        self.redis_ttl = self.getConfigurationValue('redis_ttl')
        # Get redis client module.
        if self.getConfigurationValue('redis_store'):
            mod_info = self.lumbermill.getModuleInfoById(self.getConfigurationValue('redis_store'))
            self.redis_store = mod_info['instances'][0]
        else:
            self.redis_store = None

    def castToList(self, value):
        list = []
        for x in value:
            try:
                list.append(etree.tostring(x))
            except TypeError:
                list.append(str(x))
        return list

    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        @return data: dictionary
        """
        source_field = self.getConfigurationValue('source_field', event)
        if source_field not in event:
            yield event
            return
        result = None
        if self.redis_store:
            redis_key = self.getConfigurationValue('redis_key', event)
            result = self.redis_store.get(redis_key)
        if result is None:
            xml_string = event[source_field].decode('utf8').encode('ascii', 'ignore')
            try:
                xml_root = etree.fromstring(xml_string)
                xml_tree = etree.ElementTree(xml_root)
                result =  xml_tree.xpath(self.getConfigurationValue('query', event))
                if(type(result) == list):
                    result = self.castToList(result)
                if self.redis_store:
                    self.redis_store.set(redis_key, result, self.redis_ttl)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Could not parse xml doc %s Exception: %s, Error: %s." % (xml_string, etype, evalue))
        if result:
            target_field_name = self.getConfigurationValue('target_field', event)
            event[target_field_name] = result
        yield event