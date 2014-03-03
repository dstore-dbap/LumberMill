# -*- coding: utf-8 -*-
import BaseModule
import pprint
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class StdOutSink(BaseModule.BaseModule):
    """
    Print the data dictionary to stdout.

    Configuration example:

    - StdOutSink:
        pretty_print:           # <default: True; type: boolean; is: optional>
        fields:                 # <default: ''; type: string; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def handleEvent(self, event):
        if self.getConfigurationValue('fields'):
            output = self.getConfigurationValue('fields', event)
        else:
            output = event
        if self.getConfigurationValue('pretty_print'):
            pprint.pprint(output, indent=4)
        else:
            print "%s" % output
        yield event