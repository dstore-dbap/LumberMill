# -*- coding: utf-8 -*-
import time
import datetime
import BaseThreadedModule
import BaseMultiProcessModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class AddDateTime(BaseThreadedModule.BaseThreadedModule):
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

    def handleData(self, event):
        """
        Process the event.

        @param event: dictionary
        @return data: dictionary
        """
        event[self.getConfigurationValue('target_field', event)] = datetime.datetime.utcnow().strftime(self.getConfigurationValue('format', event))
        yield event