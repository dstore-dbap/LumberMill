# -*- coding: utf-8 -*-
import Utils
import BaseThreadedModule
import pprint
import time
import Decorators


@Decorators.ModuleDocstringParser
class Spam(BaseThreadedModule.BaseThreadedModule):
    """
    Emits events as fast as possible.

    Use this module to load test GambolPutty. Also nice for testing your regexes.

    The event field can either be a simple string. This string will be used to create a default gambolputty event dict.
    If you want to provide more custom fields, you can provide a dictionary containing at least a "data" field that
    should your raw event string.

    event: Send custom event data. To send a more complex event provide a dict, use a string to send a simple event.
    sleep: Time to wait between sending events.
    events_count: Only send configured number of events. 0 means no limit.

    Configuration template:

    - Spam:
        event:                    # <default: ""; type: string||dict; is: optional>
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
        if not isinstance(self.event, dict):
            self.event = {'data': self.event}
        self.sleep = self.getConfigurationValue("sleep")

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
