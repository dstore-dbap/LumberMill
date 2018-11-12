# -*- coding: utf-8 -*-
import sys

from lxml import etree

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.mixins.ModuleCacheMixin import ModuleCacheMixin
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class XPathParser(BaseThreadedModule, ModuleCacheMixin):
    """
    Parse an xml string via xpath.

    This module supports the storage of the results in a cache. If cache is set,
    it will first try to retrieve the result from cache via the key setting.
    If that fails, it will execute the xpath query and store the result in cache.

    Configuration template:

    - XPathParser:
       source_field:                    # <type: string; is: required>
       target_field:                    # <default: "xpath_result"; type: string; is: optional>
       query:                           # <type: string; is: required>
       cache:                           # <default: None; type: None||string; is: optional>
       cache_key:                       # <default: None; type: None||string; is: optional if cache is None else required>
       cache_lock:                      # <default: 'Lumbermill:XPathParser:XPathParserLock'; type: string; is: optional>
       cache_ttl:                       # <default: 60; type: integer; is: optional>
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        BaseThreadedModule.configure(self, configuration)
        ModuleCacheMixin.configure(self)

    def _castToList(self, value):
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
        result = None
        if self.cache:
            cache_key = self.getConfigurationValue('cache_key', event)
            result = self._getFromCache(cache_key, event)
        if result is None:
            try:
                xml_string = event[source_field].decode('utf8').encode('ascii', 'ignore')
            except KeyError:
                yield event
                return
            try:
                xml_root = etree.fromstring(xml_string)
                xml_tree = etree.ElementTree(xml_root)
                result = xml_tree.xpath(self.getConfigurationValue('query', event))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Could not parse xml doc %s Exception: %s, Error: %s." % (xml_string, etype, evalue))
        if result:
            if type(result) == list:
                result = self._castToList(result)
            if self.cache and not event['lumbermill']['cache_hit']:
                self.cache.set(cache_key, result, self.cache_ttl)
            target_field_name = self.getConfigurationValue('target_field', event)
            event[target_field_name] = result
        yield event
