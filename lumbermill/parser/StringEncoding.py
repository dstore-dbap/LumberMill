# -*- coding: utf-8 -*-
import base64
from bs4 import UnicodeDammit

from BaseThreadedModule import BaseThreadedModule
from utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class StringEncoding(BaseThreadedModule):
    r"""
    This module will let you en/decode different string encodings.

    TODO: THIS MODULE IS ONLY A STUB....

    source_fields:  Input fields to en/decode. Can be a single field or a list of fields.
    target_fields:  Event field to be filled with the new data.

    Configuration template:

    - parser.StringEncoding:
       action:                          # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
       source_fields:                   # <default: 'data'; type: string||list; is: optional>
       target_fields:                   # <default: 'data'; type:string; is: optional>
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
        self.target_fields = self.getConfigurationValue('target_fields')
        self.drop_original = not self.getConfigurationValue('keep_original')
        if self.getConfigurationValue('action') == 'decode':
            self.handleEvent = self.decode
        else:
            self.handleEvent = self.encode

    def decode(self, event):
        if self.source_field in event:
            decoded_dataset = base64.b64decode(event[self.source_field])
            if self.drop_original:
                event.pop(self.source_field, None)
            event[self.target_field] = decoded_dataset
        yield event

    def encode(self, event):
        if self.source_field in event:
            encoded_dataset = base64.b64encode(event[self.source_field])
            if self.drop_original:
                event.pop(self.source_field, None)
            event[self.target_field] = encoded_dataset
        yield event

