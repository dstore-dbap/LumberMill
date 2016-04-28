# -*- coding: utf-8 -*-
import types

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class LineParser(BaseThreadedModule):
    r"""
    Line parser.

    Decode:
    Will split the data in source fields and emit parts as new events. So if e.g. data field contains:
    message-a|message-b|message-c
    you can split this field by "|" and three new events will be created with message-a, message-b and message-c as
    payload.

    The original event will be discarded.

    source_field:   Input field to split.
    seperator:      Char used as line seperator.
    target_field:   event field to be filled with the new data.

    Configuration template:

    - LineParser:
       source_field:                    # <default: 'data'; type: string||list; is: optional>
       seperator:                       # <default: '\n'; type: string; is: optional>
       target_field:                    # <default: 'data'; type:string; is: optional>
       keep_original:                   # <default: False; type: boolean; is: optional>
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')
        self.seperator = self.getConfigurationValue('seperator')
        self.target_field = self.getConfigurationValue('target_field')
        self.drop_original = not self.getConfigurationValue('keep_original')

    def handleEvent(self, event):
        if self.source_field in event:
            decoded_datasets = event[self.source_field].split(self.seperator)
            if self.drop_original:
                event.pop(self.source_field, None)
            event.update({self.target_field: decoded_datasets})
        yield event

