# -*- coding: utf-8 -*-
import types

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class OCRParser(BaseThreadedModule):
    r"""
    OCR parser.

    This parser will takes base64 encoded binary data, convert that to an image and runs an ocr over that image.

    It uses the python bindings to tesseract (https://github.com/tesseract-ocr).
    On centos this can be installed with:
    yum install tasseract tesseract-devel

    source_fields:  Input fields to split. Can be a single field or a list of fields.
    target_field:   event field to be filled with extraced texts.

    Configuration template:

    - OCRParser:
       source_fields:                   # <default: 'data'; type: string||list; is: optional>
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

