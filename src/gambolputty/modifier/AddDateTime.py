# -*- coding: utf-8 -*-
import datetime
import Utils
import BaseModule
from Decorators import ModuleDocstringParser



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

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.format = self.getConfigurationValue('format')

    def handleEvent(self, event):
        event[self.getConfigurationValue('target_field', event)] = Utils.mapDynamicValue(datetime.datetime.utcnow().strftime(self.format), event)
        yield event