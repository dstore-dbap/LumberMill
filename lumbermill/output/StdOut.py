# -*- coding: utf-8 -*-
import pprint
import time

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser
from lumbermill.utils.DynamicValues import mapDynamicValue


@ModuleDocstringParser
class StdOut(BaseThreadedModule):
    """
    Print the data dictionary to stdout.

    pretty_print: Use pythons pprint function.
    fields: Set event fields to include in pretty print output.
    format: Format of messages to send to graphite, e.g.: ['lumbermill.stats.event_rate_$(interval)s $(event_rate)'].

    Configuration template:

    - output.StdOut:
       pretty_print:                    # <default: True; type: boolean; is: optional>
       fields:                          # <default: None; type: None||list; is: optional>
       format:                          # <default: None; type: None||string; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.pretty_print = self.getConfigurationValue('pretty_print')
        self.fields = self.getConfigurationValue('fields')
        self.format = self.getConfigurationValue('format')
        self.printing = False

    def handleEvent(self, event):
        while self.printing:
            time.sleep(.0001)
        self.printing = True
        if self.format:
            output = mapDynamicValue(self.format, event)
            print("%s" % output)
        elif self.pretty_print:
            if not self.fields:
                output = event
            else:
                output = {}
                for field in self.fields:
                    try:
                        value = event[field]
                    except KeyError:
                        continue
                    output[field] = value
            pprint.pprint(output, indent=4)
        self.printing = False
        yield None
