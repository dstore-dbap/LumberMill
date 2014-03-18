# -*- coding: utf-8 -*-
import BaseModule
import pprint
from Decorators import ModuleDocstringParser
import time


@ModuleDocstringParser
class StdOutSink(BaseModule.BaseModule):
    """
    Print the data dictionary to stdout.

    Configuration example:

    - StdOutSink:
        pretty_print:           # <default: True; type: boolean; is: optional>
        format:                 # <default: ''; type: string; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.printing = False

    def handleEvent(self, event):
        while self.printing:
            time.sleep(.0001)
        self.printing = True
        if self.getConfigurationValue('format'):
            output = self.getConfigurationValue('format', event)
        else:
            output = event
        if self.getConfigurationValue('pretty_print'):
            pprint.pprint(output, indent=4)
        else:
            print "%s" % output
        self.printing = False
        yield None