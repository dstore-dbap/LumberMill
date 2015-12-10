# -*- coding: utf-8 -*-
import time

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser

@ModuleDocstringParser
class Tarpit(BaseThreadedModule):
    """
    Send an event into a tarpit before passing it on.

    Useful only for testing purposes of threading problems and concurrent access to event data.

    Configuration template:

    - Tarpit:
       delay:                           # <default: 10; type: integer; is: optional>
       receivers:
        - NextModule
    """

    module_type = "misc"
    """Set module type"""

    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        @return data: dictionary
        """
        time.sleep(self.getConfigurationValue('delay'))
        yield event