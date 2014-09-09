# -*- coding: utf-8 -*-
import time
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class Tarpit(BaseThreadedModule.BaseThreadedModule):
    """
    Send an event into a tarpit before passing it on.

    Useful only for testing purposes of threading problems and concurrent access to event data.

    Configuration example:

    - Tarpit:
        delay:          # <default: 10; type: integer; is: optional>
        receivers:
          - NextModule
    """

    module_type = "misc"
    """Set module type"""

    def fib(self, n):
        if n == 0:
            return 0
        elif n == 1:
            return 1
        else:
            return self.fib(n-1) + self.fib(n-2)

    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        @return data: dictionary
        """
        #time.sleep(self.getConfigurationValue('delay'))
        self.fib(25)
        yield event