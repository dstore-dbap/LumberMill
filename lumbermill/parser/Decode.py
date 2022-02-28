# -*- coding: utf-8 -*-
from bs4 import UnicodeDammit

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class Decode(BaseThreadedModule):
    """
    Decode 

    Decode field to specific encoding.


    Configuration template:

    - Decode:
      encoding:                        # <default: 'utf-8'; type: string; is: optional>
      source_fields:                   # <default: 'data'; type: string||list; is: optional>
      target_fields:                   # <default: None; type: None||string||list; is: optional>
      receivers:
       - NextModule
    """
    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.encoding = self.getConfigurationValue('encoding')
        self.source_fields = self.getConfigurationValue('source_fields')
        self.target_fields = self.getConfigurationValue('target_fields')

    def handleEvent(self, event):
        for idx, source_field in enumerate(self.source_fields):
            try:
              decoded_data = event[source_field].decode(self.encoding)
            except KeyError:
                continue
            except (UnicodeEncodeError, UnicodeDecodeError):
                json_string = UnicodeDammit(event[source_field]).unicode_markup
            if not self.target_fields:
                event[source_field] = decoded_data
            else:
                event[self.target_fields[idx]] = decoded_data
        yield event
