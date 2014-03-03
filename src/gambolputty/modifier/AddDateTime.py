# -*- coding: utf-8 -*-
import datetime
import BaseModule
from Decorators import ModuleDocstringParser
import pprint


@ModuleDocstringParser
class AddDateTime(BaseModule.BaseModule):
    """
    Add a field with the current datetime.

    Configuration example:

    - AddDateTime:
        target_field:        # <default: '@timestamp'; type: string; is: optional>
        format:              # <default: '%Y-%m-%dT%H:%M:%S'; type: string; is: optional>
        receivers:
          - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def handleEvent(self, event):
        event[self.getConfigurationValue('target_field', event)] = datetime.datetime.utcnow().strftime(self.getConfigurationValue('format', event))
        yield event