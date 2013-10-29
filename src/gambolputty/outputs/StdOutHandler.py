# -*- coding: utf-8 -*-
import BaseModule
import pprint
from Decorators import GambolPuttyModule

@GambolPuttyModule
class StdOutHandler(BaseModule.BaseModule):
    """
    Print the data dictionary to stdout.

    Configuration example:

    - module: StdOutHandler
      configuration:
        pretty-print: True      # <default: True; type: boolean; is: optional>
    """
    def handleData(self, data):
        if self.getConfigurationValue('pretty-print'):
            pprint.pprint(data)
        else:
            print "%s" % data
