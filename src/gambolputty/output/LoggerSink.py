# -*- coding: utf-8 -*-
import Utils
import BaseThreadedModule
import Decorators
import time


@Decorators.ModuleDocstringParser
class LoggerSink(BaseThreadedModule.BaseThreadedModule):
    """
    Send data to gambolputty logger.

    formats: Format of messages to send to logger, e.g.:
             ['############# Statistics #############',
              'Received events in %(interval)ds: %(total_count)d',
              'EventType: httpd_access_log - Hits: %(field_counts.httpd_access_log)d',
              'EventType: Unknown - Hits: %(field_counts.Unknown)d']

    Configuration template:

    - LoggerSink:
        formats:    # <type: list; is: required>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
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