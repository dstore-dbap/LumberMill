# -*- coding: utf-8 -*-
import datetime
import BaseModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class AddDateTime(BaseModule.BaseModule):
    """
    Add a field with the current datetime.

    Configuration example:

    - module: AddDateTime
      configuration:
        target_field: 'my_timestamp' # <default: '@timestamp'; type: string; is: optional>
        format: '%Y-%M-%dT%H:%M:%S'  # <default: '%Y-%m-%dT%H:%M:%S'; type: string; is: optional>
      receivers:
        - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def handleEvent(self, event):
        event[self.getConfigurationValue('target_field', event)] = datetime.datetime.utcnow().strftime(self.getConfigurationValue('format', event))
        self.sendEventToReceivers(event)