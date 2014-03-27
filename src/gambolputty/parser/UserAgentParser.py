# -*- coding: utf-8 -*-
import sys
import httpagentparser
import types
import BaseModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class UserAgentParser(BaseModule.BaseModule):
    r"""
    Parse http useragent string

    source_fields:  Input field to parse.

    Configuration example:

    - LineParser:
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
