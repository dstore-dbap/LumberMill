# -*- coding: utf-8 -*-
import Utils
import BaseThreadedModule
import time
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class Spam(BaseThreadedModule.BaseThreadedModule):
    """
    Emits events as fast as possible.

    Use this module to load test GambolPutty.

    event: Send custom event data.
    sleep: Time to wait between sending events.
    events_count: Only send configured number of events. 0 means no limit.

    Configuration example:

    - module: Spam
      event: {'Lobster': 'Thermidor', 'Truffle': 'Pate'}  # <default: {}; type: dict; is: optional>
      sleep: 0                                            # <default: 0; type: int||float; is: optional>
      events_count: 1000                                  # <default: 0; type: int; is: optional>
      receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""

    def run(self):
        counter = 0
        max_events_count = self.getConfigurationValue("events_count")
        while self.alive:
            event = Utils.getDefaultEventDict(self.getConfigurationValue("event"), caller_class_name=self.__class__.__name__)
            self.sendEvent(event)
            if self.getConfigurationValue("sleep"):
                time.sleep(self.getConfigurationValue("sleep"))
            counter += 1
            if (counter - max_events_count == 0):
                self.gp.shutDown()
