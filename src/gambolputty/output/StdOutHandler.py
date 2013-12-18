# -*- coding: utf-8 -*-
import BaseModule
import pprint
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class StdOutHandler(BaseModule.BaseModule):
    """
    Print the data dictionary to stdout.

    Configuration example:

    - module: StdOutHandler
      configuration:
        pretty_print: True      # <default: True; type: boolean; is: optional>
      receivers:
        - NextModule
    """

    module_type = "output"
    """Set module type"""

    def handleEvent(self, event):
        if self.getConfigurationValue('pretty_print'):
            pprint.pprint(event)
        else:
            print "%s" % event