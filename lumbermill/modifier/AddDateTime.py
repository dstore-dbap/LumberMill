# -*- coding: utf-8 -*-
import time

import datetime

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class AddDateTime(BaseThreadedModule):
    """
    Add a field with the current datetime.

    Configuration template:

    - AddDateTime:
       target_field:                    # <default: '@timestamp'; type: string; is: optional>
       format:                          # <default: '%Y-%m-%dT%H:%M:%S'; type: string; is: optional>
       receivers:
        - NextModule
    """
    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.format = self.getConfigurationValue('format')
        self.target_field = self.getConfigurationValue('target_field')

    def handleEvent(self, event):
        event[self.target_field] = datetime.datetime.utcnow().strftime(self.format)
        yield event