# -*- coding: utf-8 -*-
from lxml import etree
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class XPathParser(BaseThreadedModule.BaseThreadedModule):
    """
    Parse an xml string via xpath.

    Configuration example:

    - module: XPathParser
      configuration:
        source-field: 'xml_data'                                # <type: string; is: required>
        query:  '//Item[@%(server_name)s]/@NodeDescription'     # <type: string; is: required>
    """

    def castToList(self, value):
        return [str(x) for x in value]

    def handleData(self, data):
        """
        Process the event.

        @param data: dictionary
        @return data: dictionary
        """
        source_field = self.getConfigurationValue('source-field', data)
        if source_field not in data:
            return data
        result = self.getRedisValue(self.getConfigurationValue('redis-key', data))
        if result == None:
            xml_string = data[source_field].decode('utf8').encode('ascii', 'ignore')
            xml_root = etree.fromstring(xml_string)
            xml_tree = etree.ElementTree(xml_root)
            result =  xml_tree.xpath(self.getConfigurationValue('query', data))
            if(type(result) == list):
                result = self.castToList(result)
            self.setRedisValue(self.getConfigurationValue('redis-key', data), result, self.getConfigurationValue('redis-ttl'))
        if result:
            target_field_name = self.getConfigurationValue('target-field', data) if 'target-field' in self.configuration_data else "gambolputty_xpath"
            data[target_field_name] = result
        return data