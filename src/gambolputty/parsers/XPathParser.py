# -*- coding: utf-8 -*-
from lxml import etree
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class XPathParser(BaseThreadedModule.BaseThreadedModule):
    """
    Parse an xml string via xpath.

    This module supports the storage of the results in an redis db. If redis-client is set,
    it will first try to retrieve the result from redis via the key setting.
    If that fails, it will execute the xpath query and store the result in redis.

    Configuration example:

    - module: XPathParser
      configuration:
        source_field: 'xml_data'                                # <type: string; is: required>
        target_field: xpath                                     # <default: "gambolputty_xpath"; type: string; is: optional>
        query:  '//Item[@%(server_name)s]/@NodeDescription'     # <type: string; is: required>
        redis_client: RedisClientName           # <default: ""; type: string; is: optional>
        redis_key: HttpRequest%(server_name)s   # <default: ""; type: string; is: optional>
        redis_ttl: 600                          # <default: 60; type: integer; is: optional>
    """

    def castToList(self, value):
        return [str(x) for x in value]

    def handleData(self, data):
        """
        Process the event.

        @param data: dictionary
        @return data: dictionary
        """
        source_field = self.getConfigurationValue('source_field', data)
        if source_field not in data:
            return data
        result = self.getRedisValue(self.getConfigurationValue('redis_key', data))
        if result == None:
            xml_string = data[source_field].decode('utf8').encode('ascii', 'ignore')
            xml_root = etree.fromstring(xml_string)
            xml_tree = etree.ElementTree(xml_root)
            result =  xml_tree.xpath(self.getConfigurationValue('query', data))
            if(type(result) == list):
                result = self.castToList(result)
            self.setRedisValue(self.getConfigurationValue('redis_key', data), result, self.getConfigurationValue('redis_ttl'))
        if result:
            target_field_name = self.getConfigurationValue('target_field', data)
            data[target_field_name] = result
        return data