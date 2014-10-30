# -*- coding: utf-8 -*-
import Utils
import BaseThreadedModule
import pprint
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

    Configuration template:

    - Spam:
        event:                    # <default: {}; type: dict; is: optional>
        sleep:                    # <default: 0; type: int||float; is: optional>
        events_count:             # <default: 0; type: int; is: optional>
        receivers:
          - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.event = self.getConfigurationValue("event")
        self.sleep = self.getConfigurationValue("sleep")
        #pprint.pprint(self.configuration_data)

    def run(self):
        counter = 0
        max_events_count = self.getConfigurationValue("events_count")
        while self.alive:
            event = Utils.getDefaultEventDict(self.event, caller_class_name=self.__class__.__name__) # self.getConfigurationValue("event")
            self.sendEvent(event)
            if self.sleep > 0:
                time.sleep(self.sleep)
            counter += 1
            if (counter - max_events_count == 0):
                time.sleep(2)
                self.gp.shutDown()
