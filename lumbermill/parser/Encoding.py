# -*- coding: utf-8 -*-
import base64
from bs4 import UnicodeDammit

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class Encoding(BaseThreadedModule):
    r"""
    This module will let you en/decode different string encodings.

    encoding:       Encoding to use when de/encode.
    source_fields:  Input field(s) to en/decode. Can be a single field or a list of fields.
    target_fields:  Event field(s) to be filled with the new data.

    Configuration template:

    - parser.Encoding:
       action:                          # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
       encoding:                        # <default: 'utf-8'; type: string; is: optional>
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
        self.encoding = self.getConfigurationValue('encoding')
        self.source_fields = self.getConfigurationValue('source_fields')
        self.target_fields = self.getConfigurationValue('target_fields')
        self.drop_original = not self.getConfigurationValue('keep_original') and self.source_fields != self.target_fields
        if self.getConfigurationValue('action') == 'decode':
            if type(self.target_fields) == 'list':
                self.handleEvent = self.decodeFields
            else:
                self.handleEvent = self.decodeField
        else:
            if type(self.target_fields) == 'list':
                self.handleEvent = self.encodeFields
            else:
                self.handleEvent = self.encodeField

    def decodeFields(self, event):
        for idx, source_field in enumerate(self.source_fields):
            try:
                decoded_data = event[source_field].decode(self.encoding)
            except KeyError:
                continue
            event[self.target_fields[idx]] = decoded_data
            if self.drop_original:
                event.pop(self.source_field, None)
        yield event

    def decodeField(self, event):
        try:
            decoded_data = event[self.source_fields].decode(self.encoding)
            event[self.target_fields] = decoded_data
            if self.drop_original:
                event.pop(self.source_fields, None)
        except KeyError:
            pass
        yield event

    def encodeFields(self, event):
        for idx, source_field in enumerate(self.source_fields):
            try:
              encoded_data = event[source_field].encode(self.encoding)
            except KeyError:
                continue
            event[self.target_fields[idx]] = encoded_data
            if self.drop_original:
                event.pop(self.source_field, None)
        yield event

    def encodeField(self, event):
        try:
            encoded_data = event[self.source_fields].encode(self.encoding)
            event[self.target_fields] = encoded_data
            if self.drop_original:
                event.pop(self.source_fields, None)
        except KeyError:
            pass
        yield event