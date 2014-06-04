# -*- coding: utf-8 -*-
import BaseModule
import pprint
import Utils
from Decorators import ModuleDocstringParser
import time

@ModuleDocstringParser
class StdOutSink(BaseModule.BaseModule):
    """
    Print the data dictionary to stdout.

    pretty_print: Use pythons pprint function.
    format: Format of messages to send to graphite, e.g.: ['gambolputty.stats.event_rate_%(interval)ds %(event_rate)s'].

    Configuration example:

    - StdOutSink:
        pretty_print:           # <default: True; type: boolean; is: optional>
        format:                 # <default: None; type: None||string; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.format = self.getConfigurationValue('format')
        self.printing = False

    def handleEvent(self, event):
        while self.printing:
            time.sleep(.0001)
        self.printing = True
        if self.format:
            output = Utils.mapDynamicValue(self.format, event)
            # If mapping failed, no need to print anything.
            if not output:
                self.printing = False
                return
        else:
            output = event
        if self.getConfigurationValue('pretty_print'):
            pprint.pprint(output, indent=4)
        else:
            print "%s" % output
        self.printing = False
        yield None