# -*- coding: utf-8 -*-
import BaseThreadedModule
import pprint
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class StdOutHandler(BaseThreadedModule.BaseThreadedModule):
    """
    Print the data dictionary to stdout.

    Configuration example:

    - module: StdOutHandler
      configuration:
        pretty_print: True      # <default: True; type: boolean; is: optional>
      receivers:
        - NextModule
    """
    def handleData(self, data):
        if self.getConfigurationValue('pretty_print'):
            pprint.pprint(data)
        else:
            print "%s" % data
