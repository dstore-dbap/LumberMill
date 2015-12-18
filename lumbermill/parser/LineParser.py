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

    source_fields:  Input fields to split. Can be a single field or a list of fields.
    seperator:      Char used as line seperator.
    target_field:   event field to be filled with the new data.

    Configuration template:

    - LineParser:
       source_fields:                   # <default: 'data'; type: string||list; is: optional>
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
        self.source_fields = self.getConfigurationValue('source_fields')
        # Allow single string as well.
        if isinstance(self.source_fields, types.StringTypes):
            self.source_fields = [self.source_fields]
        self.seperator = self.getConfigurationValue('seperator')
        self.target_field = self.getConfigurationValue('target_field')
        self.drop_original = not self.getConfigurationValue('keep_original')

    def handleEvent(self, event):
        for source_field in self.source_fields:
            if source_field not in event:
                continue
            decoded_datasets = event[source_field].split(self.seperator)
            copy_event = False
            for decoded_data in decoded_datasets:
                if copy_event:
                    event = event.copy()
                copy_event = True
                if self.drop_original:
                    event.pop(source_field, None)
                event.update({self.target_field: decoded_data})
                yield event

