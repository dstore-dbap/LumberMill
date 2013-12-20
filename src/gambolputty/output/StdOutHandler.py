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
        pretty_print: True          # <default: True; type: boolean; is: optional>
        fields: '%(@timestamp)s'    # <default: ''; type: string; is: optional>
      receivers:
        - NextModule
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