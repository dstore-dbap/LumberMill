# -*- coding: utf-8 -*-
import time

import datetime

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class AddDateTime(BaseThreadedModule):
    """
    Add a field with a datetime.

    If source_fields is not set, datetime will be based on current time.
    If source_fields is set, event will be searched for each source_field.
    If found, all source_formats will be applied, to parse the date.
    First successful conversion will win.


    Configuration template:

    - AddDateTime:
       source_fields:                   # <default: None; type: None||list; is: optional>
       source_formats:                  # <default: None; type: None||list; is: required if source_fields is not None else optional>
       target_field:                    # <default: '@timestamp'; type: string; is: optional>
       target_format:                   # <default: '%Y-%m-%dT%H:%M:%S'; type: string; is: optional>
       receivers:
        - NextModule
    """
    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_fields = self.getConfigurationValue('source_fields')
        self.source_formats = self.getConfigurationValue('source_formats')
        self.target_format = self.getConfigurationValue('target_format')
        self.target_field = self.getConfigurationValue('target_field')
        if self.source_fields:
            self.handleEvent = self.handleEventWithSourceFields

    def handleEvent(self, event):
        event[self.target_field] = datetime.datetime.utcnow().strftime(self.target_format)
        yield event

    def handleEventWithSourceFields(self, event):
        for source_field in self.source_fields:
            try:
                time_field = event[source_field]
            except KeyError:
                continue
            for source_format in self.source_formats:
                try:
                    date_time = datetime.datetime.strptime(time_field, source_format)
                except ValueError:
                    continue
                event[self.target_field] = date_time.strftime(self.target_format)
        yield event