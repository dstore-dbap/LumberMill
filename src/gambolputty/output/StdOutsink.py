# -*- coding: utf-8 -*-
import BaseModule
import pprint
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class StdOutSink(BaseModule.BaseModule):
    """
    Print the data dictionary to stdout.

    Configuration example:

    - module: StdOutSink
      pretty_print: True          # <default: True; type: boolean; is: optional>
      fields: '%(@timestamp)s'    # <default: ''; type: string; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def handleEvent(self, event):
        if self.getConfigurationValue('fields'):
            output = self.getConfigurationValue('fields', event)
        else:
            output = event
        if self.getConfigurationValue('pretty_print'):
            pprint.pprint(output)
        else:
            print "%s" % output
        yield event