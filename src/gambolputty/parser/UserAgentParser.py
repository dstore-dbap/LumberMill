# -*- coding: utf-8 -*-
import sys
import httpagentparser
import types
import BaseModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class UserAgentParser(BaseModule.BaseModule):
    r"""
    Parse http user agent string

    A string like:

        "Mozilla/5.0 (Linux; U; Android 2.3.5; en-in; HTC_DesireS_S510e Build/GRJ90) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"

    will produce this dictionary:

        {'dist': {'version': '2.3.5', 'name': 'Android'},
         'os': {'name': 'Linux'},
         'browser': {'version': '4.0', 'name': 'Safari'}}

    source_fields:  Input field to parse.
    target_field: field to update with parsed info fields.

    Configuration template:

    - UserAgentParser:
        source_fields:               # <type: string||list; is: required>
        target_field:                # <default: 'user_agent_info'; type:string; is: optional>
        receivers:
          - NextHandler
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.source_fields = self.getConfigurationValue('source_fields')
        # Allow single string as well.
        if isinstance(self.source_fields, types.StringTypes):
            self.source_fields = [self.source_fields]
        self.target_field = self.getConfigurationValue('target_field')

    def handleEvent(self, event):
        for source_field in self.source_fields:
            if source_field not in event:
                continue
            event[self.target_field] = httpagentparser.detect(event[source_field])
        yield event
