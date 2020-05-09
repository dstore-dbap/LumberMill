# -*- coding: utf-8 -*-
import base64

from BaseThreadedModule import BaseThreadedModule
from utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class Base64(BaseThreadedModule):
    r"""
    This module will let you en/decode base64 data.

    source_fields:  Input fields to split. Can be a single field or a list of fields.
    target_fields:   event field to be filled with the new data.

    Configuration template:

    - parser.Base64:
       action:                          # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
       source_field:                    # <default: 'data'; type: string||list; is: optional>
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
        self.target_field = self.getConfigurationValue('target_field')
        self.drop_original = not self.getConfigurationValue('keep_original')
        if self.getConfigurationValue('action') == 'decode':
            self.handleEvent = self.decodeBase64
        else:
            self.handleEvent = self.encodeBase64

    def decodeBase64(self, event):
        if self.source_field in event:
            decoded_dataset = base64.b64decode(event[self.source_field])
            if self.drop_original:
                event.pop(self.source_field, None)
            event[self.target_field] = decoded_dataset
        yield event

    def encodeBase64(self, event):
        if self.source_field in event:
            encoded_dataset = base64.b64encode(event[self.source_field])
            if self.drop_original:
                event.pop(self.source_field, None)
            event[self.target_field] = encoded_dataset
        yield event

