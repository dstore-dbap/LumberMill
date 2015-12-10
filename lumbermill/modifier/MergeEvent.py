# -*- coding: utf-8 -*-
import re
import os
import sys
import collections

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class MergeEvent(BaseThreadedModule):
    """
    Merge multiple event into a single one.

    In most cases, inputs will split an incoming stream at some kind of delimiter to produce events.
    Sometimes, the delimiter also occurs in the event data itself and splitting here is not desired.
    To mitigate this problem, this module can merge these fragmented events based on some configurable rules.

    Each incoming event will be buffered in a queue identified by <buffer_key>.
    If a new event arrives and <pattern> does not match for this event, the event will be appended to the buffer.
    If a new event arrives and <pattern> matches for this event, the buffer will be flushed prior to appending the event.
    After <flush_interval_in_secs> the buffer will also be flushed.
    Flushing the buffer will concatenate all contained event data to form one single new event.

    buffer_key: key to distinguish between different input streams

    buffer_key: A key to correctly group events.
    buffer_size: Maximum size of events in buffer. If size is exceeded a flush will be executed.
    flush_interval_in_secs: If interval is reached, buffer will be flushed.
    pattern: Pattern to match new events. If pattern matches, a flush will be executed prior to appending the event to buffer.
    glue: Join event data with glue as separator.

    Configuration template:

    - MergeEvent:
       buffer_key:                      # <default: "$(lumbermill.received_from)"; type: string; is: optional>
       buffer_size:                     # <default: 100; type: integer; is: optional>
       flush_interval_in_secs:          # <default: 1; type: None||integer; is: required if pattern is None else optional>
       pattern:                         # <default: None; type: None||string; is: required if flush_interval_in_secs is None else optional>
       match_field:                     # <default: "data"; type: string; is: optional>
       glue:                            # <default: ""; type: string; is: optional>
       receivers:
        - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.logstash_patterns = {}
        self.readLogstashPatterns()
        self.pattern = self.getConfigurationValue('pattern')
        if self.pattern:
            try:
                self.pattern = self.replaceLogstashPatterns(self.pattern)
                self.pattern = re.compile(self.pattern)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("RegEx error for pattern %s. Exception: %s, Error: %s." % (self.pattern, etype, evalue))
                self.lumbermill.shutDown()
        self.match_field = self.getConfigurationValue('match_field')
        self.buffer_size = self.getConfigurationValue('buffer_size')
        self.flush_interval_in_secs = self.getConfigurationValue('flush_interval_in_secs')
        self.glue = self.getConfigurationValue('glue')

    def readLogstashPatterns(self):
        path = "%s/../assets/grok_patterns" % os.path.dirname(os.path.realpath(__file__))
        for (dirpath, dirnames, filenames) in os.walk(path):
            for filename in filenames:
                lines = [line.strip() for line in open('%s%s%s' % (dirpath, os.sep, filename))]
                for line_no, line in enumerate(lines):
                    if line == "" or line.startswith('#'):
                        continue
                    try:
                        pattern_name, pattern = line.split(' ', 1)
                        self.logstash_patterns[pattern_name] = pattern
                    except:
                        etype, evalue, etb = sys.exc_info()
                        self.logger.warning("Could not read logstash pattern in file %s%s%s, line %s. Exception: %s, Error: %s." % (dirpath,  os.sep, filename, line_no+1, etype, evalue))

    def replaceLogstashPatterns(self, regex_pattern):
        pattern_name_re = re.compile('%\{(.*?)\}')
        for match in pattern_name_re.finditer(regex_pattern):
            for pattern_name in match.groups():
                try:
                    logstash_pattern = self.replaceLogstashPatterns(self.logstash_patterns[pattern_name])
                    regex_pattern = regex_pattern.replace('%%{%s}' % pattern_name, logstash_pattern)
                except KeyError:
                    self.logger.warning("Could not parse logstash pattern %s. Pattern name not found in pattern files." % (pattern_name))
                    continue
        return regex_pattern

    def initAfterFork(self):
        # As the buffer uses a threaded timed function to flush its buffer and thread will not survive a fork, init buffer here.
        self.buffers = collections.defaultdict(lambda: Utils.Buffer(flush_size=self.buffer_size,
                                                                    callback=self.sendMergedEvent,
                                                                    interval=self.flush_interval_in_secs,
                                                                    maxsize=self.buffer_size))
        BaseThreadedModule.initAfterFork(self)

    def handleEvent(self, event):
        key = self.getConfigurationValue("buffer_key", event)
        # No pattern was defined, to merging of event data will only be based on the buffer key.
        if not self.pattern:
            self.buffers[key].append(event)
            yield None
            return
        # If pattern matches create new buffer with current key.
        if self.pattern.search(event[self.match_field]):
            # If a buffer with current key exists, flush it before appending again.
            if self.buffers[key].bufsize() > 0:
                self.buffers[key].flush()
            self.buffers[key].append(event)
            yield None
        # Append to existing buffer.
        elif self.buffers[key].bufsize() > 0:
            self.buffers[key].append(event)
            yield None
        # No buffer exists, so just pass this event on to next module.
        else:
            yield event

    def sendMergedEvent(self, events):
        if len(events) == 1:
            self.sendEvent(events[0])
            return True
        else:
            parent_event = events[0]
            parent_event['data'] = self.glue.join([event["data"] for event in events])
            caller_class_name = parent_event["lumbermill"].get("source_module", None)
            received_from = parent_event["lumbermill"].get("received_from", None)
            merged_event = Utils.getDefaultEventDict(parent_event, caller_class_name=caller_class_name, received_from=received_from)
            self.sendEvent(merged_event)
            return True