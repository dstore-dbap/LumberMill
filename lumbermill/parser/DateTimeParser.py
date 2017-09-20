# -*- coding: utf-8 -*-
import sys
import datetime

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class DateTimeParser(BaseThreadedModule):
    """
    Parse a string to a time object an back again.

    Configuration template:

    - DateTimeParser:
       source_field:                    # <type: string; is: required>
       source_date_pattern:             # <type: string; is: required>
       target_field:                    # <default: None; type: None||string; is: optional>
       target_date_pattern:             # <type: string; is: required>
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')
        self.source_date_pattern = self.getConfigurationValue('source_date_pattern')
        self.target_field = self.getConfigurationValue('target_field') if self.getConfigurationValue('target_field') else self.source_field
        self.target_date_pattern = self.getConfigurationValue('target_date_pattern')

    def handleEvent(self, event):
        try:
            datetime_object = datetime.datetime.strptime(event[self.source_field], self.source_date_pattern)
            event[self.target_field] = datetime_object.strftime(self.target_date_pattern)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not parse datetime %s with pattern %s. Exception: %s, Error: %s." % (event[self.source_field], self.source_date_pattern, etype, evalue))
        yield event