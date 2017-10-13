# -*- coding: utf-8 -*-
import sys
import datetime
import pytz

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
       source_timezone:                 # <default: 'utc'; type: string; is: optional>
       target_field:                    # <default: None; type: None||string; is: optional>
       target_date_pattern:             # <type: string; is: required>
       target_timezone:                 # <default: 'utc'; type: string; is: optional>
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
        try:
            self.source_timezone = pytz.timezone(self.getConfigurationValue('source_timezone'))
        except pytz.UnknownTimeZoneError:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Unknown source timezone %s. Exception: %s, Error: %s." % (self.getConfigurationValue('source_timezone'), etype, evalue))
            self.lumbermill.shutDown()
        self.target_field = self.getConfigurationValue('target_field') if self.getConfigurationValue('target_field') else self.source_field
        self.target_date_pattern = self.getConfigurationValue('target_date_pattern')
        try:
            self.target_timezone = pytz.timezone(self.getConfigurationValue('target_timezone'))
        except pytz.UnknownTimeZoneError:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Unknown target timezone %s. Exception: %s, Error: %s." % (self.getConfigurationValue('target_timezone'), etype, evalue))
            self.lumbermill.shutDown()

    def handleEvent(self, event):
        if self.source_field in event:
            try:
                datetime_object = datetime.datetime.strptime(event[self.source_field], self.source_date_pattern)
                if self.source_timezone != self.target_timezone:
                    datetime_object = self.source_timezone.localize(datetime_object).astimezone(self.target_timezone)
                event[self.target_field] = datetime_object.strftime(self.target_date_pattern)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Could not parse datetime %s with pattern %s. Exception: %s, Error: %s." % (event[self.source_field], self.source_date_pattern, etype, evalue))
        yield event