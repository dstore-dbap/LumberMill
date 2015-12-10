# -*- coding: utf-8 -*-
import time

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class Spam(BaseThreadedModule):
    """
    Emits events as fast as possible.

    Use this module to load test LumberMill. Also nice for testing your regexes.

    The event field can either be a simple string. This string will be used to create a default lumbermill event dict.
    If you want to provide more custom fields, you can provide a dictionary containing at least a "data" field that
    should your raw event string.

    events: Send custom event data. For single events, use a string or a dict. If a string is provided, the contents will
            be put into the events data field.
            if a dict is provided, the event will be populated with the dict fields.
            For multiple events, provide a list of stings or dicts.
    sleep: Time to wait between sending events.
    events_count: Only send configured number of events. 0 means no limit.

    Configuration template:

    - Spam:
       event:                           # <default: ""; type: string||list||dict; is: optional>
       sleep:                           # <default: 0; type: int||float; is: optional>
       events_count:                    # <default: 0; type: int; is: optional>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.events = self.getConfigurationValue("event")
        if not isinstance(self.events, list):
            self.events = [self.events]
        self.sleep = self.getConfigurationValue("sleep")
        self.max_events_count = self.getConfigurationValue("events_count")

    def initAfterFork(self):
        BaseThreadedModule.initAfterFork(self)
        # Calculate event count when running in multiple processes.
        if self.max_events_count == 0:
            return
        self.max_events_count = int(self.getConfigurationValue("events_count")/self.lumbermill.getWorkerCount())
        if self.lumbermill.is_master():
            remainder = self.getConfigurationValue("events_count") % self.lumbermill.getWorkerCount()
            self.max_events_count += remainder
        if self.max_events_count == 0:
            self.shutDown()

    def run(self):
        counter = 0
        while self.alive:
            for event_data in self.events:
                if isinstance(event_data, str):
                    event = Utils.getDefaultEventDict({'data': event_data}, caller_class_name=self.__class__.__name__)
                elif isinstance(event_data, dict):
                    event = Utils.getDefaultEventDict(event_data, caller_class_name=self.__class__.__name__) # self.getConfigurationValue("event")
                self.sendEvent(event)
                if self.sleep > 0:
                    time.sleep(self.sleep)
                if self.max_events_count == 0:
                    continue
                counter += 1
                if (counter - self.max_events_count == 0):
                    time.sleep(2)
                    self.alive = False
        self.lumbermill.shutDown()