# -*- coding: utf-8 -*-
import time

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class Logger(BaseThreadedModule):
    """
    Send data to logger.

    formats: Format of messages to send to logger, e.g.:
             ['############# Statistics #############',
              'Received events in $(interval)s: $(total_count)',
              'EventType: httpd_access_log - Hits: $(field_counts.httpd_access_log)',
              'EventType: Unknown - Hits: $(field_counts.Unknown)']

    Configuration template:

    - output.Logger:
       formats:                         # <type: list; is: required>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.formats = self.getConfigurationValue('formats')
        self.printing = False

    def handleEvent(self, event):
        while self.printing:
            time.sleep(.0001)
        self.printing = True
        for format in self.formats:
            output = self.mapDynamicValue(format, event)
            if not output:
                continue
            self.logger.info("%s" % (output))
        self.printing = False
        yield None
