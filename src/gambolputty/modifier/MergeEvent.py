# -*- coding: utf-8 -*-
import re
import sys
import collections
import Utils
import BaseModule
from Decorators import ModuleDocstringParser


@ModuleDocstringParser
class MergeEvent(BaseModule.BaseModule):
    """
    Merge multiple event into a single one.

    In most cases, inputs will split in incoming stream at some kind of delimiter to produce events.
    Sometimes, the delimiter also occurs in the event data and splitting here is not desired.
    To mitigate this problem, this module can merge events based on some configurable rules.

    Each incoming event will be buffered in a queue identified by <buffer_key>.
    If a new event arrives and <pattern> matches for this event, the buffer will be flushed and the event appended to the now
    empty buffer.
    After <flush_interval_in_secs> the buffer will also be flushed.
    Flushing the buffer will concatenate all contained event data to form one single new event.

    buffer_key: key to distinguish between different input streams

    buffer_key: A key to correctly group events.
    buffer_size: Maximum size of events in buffer. If size is exceeded a flush will be executed.
    flush_interval_in_secs: If interval is reached, buffer will be flushed.
    pattern: Pattern to match new events. If pattern matches, a flush will be executed prior to appending the event to buffer.

    Configuration example:

    - MergeEvent:
        buffer_key:                 # <default: "%(gambolputty.received_from)s"; type: string; is: optional>
        buffer_size:                # <default: 50; type: integer; is: optional>
        flush_interval_in_secs:     # <default: None; type: None||integer; is: required if pattern is None else optional>
        pattern:                    # <default: None; type: None||string; is: required if flush_interval_in_secs is None else optional>
        receivers:
          - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.pattern = self.getConfigurationValue('pattern')
        if self.pattern:
            try:
                self.pattern = re.compile(self.getConfigurationValue('pattern'))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sRegEx error for pattern %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue('pattern'), etype, evalue, Utils.AnsiColors.ENDC))
                self.gp.shutDown()
        self.buffer_size = self.getConfigurationValue('buffer_size')
        self.flush_interval_in_secs = self.getConfigurationValue('flush_interval_in_secs')
        self.buffers = collections.defaultdict(lambda: Utils.Buffer(self.buffer_size, self.sendMergedEvent, self.flush_interval_in_secs))

    def handleEvent(self, event):
        key = self.getConfigurationValue("buffer_key", event)
        if self.pattern and self.pattern.search(event['data']):
            self.buffers[key].flush()
        self.buffers[key].append(event)
        yield None

    def sendMergedEvent(self, events):
        if len(events) == 1:
            self.sendEvent(events[0])
        else:
            merged_event_data = ""
            for event in events:
                merged_event_data = "%s%s" % (merged_event_data, event["data"])
            caller_class_name = event["gambolputty"].get("source_module", None)
            received_from = event["gambolputty"].get("received_from", None)
            merged_event = Utils.getDefaultEventDict({"data": merged_event_data}, caller_class_name=caller_class_name, received_from=received_from)
            self.sendEvent(merged_event)