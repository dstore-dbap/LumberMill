# -*- coding: utf-8 -*-
import BaseThreadedModule
import pprint
from Decorators import ModuleDocstringParser
import StatisticCollector

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

    module_type = "output"
    """Set module type"""

    def handleData(self, event):
        if self.getConfigurationValue('pretty_print'):
            pprint.pprint(event)
        else:
            print "%s" % event
        yield