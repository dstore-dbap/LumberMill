# -*- coding: utf-8 -*-
import urllib
import urlparse

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class UrlParser(BaseThreadedModule):
    """
    Urlencode or decode an event field and extract url parameters.

    action: Either encode or decode data.
    source_field: Event field to en/decode.
    target_field: Event field to update with en/decode result. If not set source will be replaced.
    parse_querystring: Parse url for query parameters and extract them.
    querystring_target_field: Event field to update with url parameters.
    querystring_prefix: Prefix string to prepend to url parameter keys.

    Configuration template:

    - UrlParser:
       action:                          # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
       source_field:                    # <type: string; is: required>
       target_field:                    # <default: None; type: None||string; is: optional>
       parse_querystring:               # <default: False; type: boolean; is: optional>
       querystring_target_field:        # <default: None; type: None||string; is: optional>
       querystring_prefix:              # <default: None; type: None||string; is: optional>
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')
        if not self.getConfigurationValue('target_field'):
            self.target_field = self.source_field
        else:
            self.target_field = self.getConfigurationValue('target_field')
        self.parse_querystring = self.getConfigurationValue('parse_querystring')
        self.querystring_target_field = self.getConfigurationValue('querystring_target_field')
        self.querystring_prefix = self.getConfigurationValue('querystring_prefix')
        if self.getConfigurationValue('action') == 'decode':
            self.handleEvent = self.decodeEvent
        else:
            self.handleEvent = self.encodeEvent

    def decodeEvent(self, event):
        if self.source_field in event:
            #try:
            #    decoded_field = urllib.unquote(event[self.source_field]).decode('utf8')
            #except UnicodeDecodeError:
            #    decoded_field = urllib.unquote(unicode(event[self.source_field]))
            decoded_field = urllib.unquote(unicode(event[self.source_field]))
            parsed_result = urlparse.urlparse('%s' % decoded_field)
            parsed_url = {'scheme': parsed_result.scheme, 'path': parsed_result.path, 'params': parsed_result.params, 'query': parsed_result.query}
            event[self.target_field] = parsed_url
            if self.parse_querystring:
                query_params_dict = urlparse.parse_qs(parsed_result.query)
                if self.querystring_prefix:
                    query_params_dict = dict(map(lambda (key, value): ("%s%s" % (self.querystring_prefix, str(key)), value), query_params_dict.items()))
                if self.querystring_target_field:
                    event[self.querystring_target_field] = query_params_dict
                else:
                    event.update(query_params_dict)
        yield event

    def encodeEvent(self, event):
        if self.source_field in event:
            urllib.quote(event[self.source_field]).encode('utf8')
        yield event