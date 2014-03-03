# -*- coding: utf-8 -*-
import time
import BaseThreadedModule
import BaseModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class Tarpit(BaseModule.BaseModule):
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

    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        @return data: dictionary
        """
        #print "aaa %s" % BaseModule.BaseModule.hasPendingEvent()
        time.sleep(self.getConfigurationValue('delay', event))
        #print "bbb %s" % BaseModule.BaseModule.hasPendingEvent()
        yield event