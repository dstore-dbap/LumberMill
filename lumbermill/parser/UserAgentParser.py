# -*- coding: utf-8 -*-
import types

from ua_parser import user_agent_parser

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Buffers import MemoryCache
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class UserAgentParser(BaseThreadedModule):
    r"""
    Parse http user agent string

    A string like:

        "Mozilla/5.0 (Linux; U; Android 2.3.5; en-in; HTC_DesireS_S510e Build/GRJ90) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"

    will produce this dictionary:

    'user_agent_info': {   'device': {   'family': u'HTC DesireS'},
                           'os': {   'family': 'Android',
                                     'major': '2',
                                     'minor': '3',
                                     'patch': '5',
                                     'patch_minor': None},
                           'user_agent': {   'family': 'Android',
                                             'major': '2',
                                             'minor': '3',
                                             'patch': '5'}}}

    source_fields:  Input field to parse.
    target_field: field to update with parsed info fields.

    Configuration template:

    - UserAgentParser:
       source_fields:                   # <type: string||list; is: required>
       target_field:                    # <default: 'user_agent_info'; type:string; is: optional>
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_fields = self.getConfigurationValue('source_fields')
        # Allow single string as well.
        if isinstance(self.source_fields, types.StringTypes):
            self.source_fields = [self.source_fields]
        self.target_field = self.getConfigurationValue('target_field')
        self.in_mem_cache = MemoryCache(size=1000)

    def handleEvent(self, event):
        for source_field in self.source_fields:
            if source_field not in event:
                continue
            # Try to get it from cache.
            try:
                ua_info = self.in_mem_cache.get(event[source_field])
            except KeyError:
                # Drop the 'string' field to avoid duplicate data.
                ua_info = user_agent_parser.Parse(event[source_field])
                if 'string' in ua_info:
                    ua_info.pop('string')
                self.in_mem_cache.set(event[source_field], ua_info)
            event[self.target_field] = ua_info
        yield event
