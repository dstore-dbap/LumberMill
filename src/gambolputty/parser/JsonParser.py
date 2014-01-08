# -*- coding: utf-8 -*-
import sys
import BaseModule
import simplejson as json
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class JsonParser(BaseModule.BaseModule):
    """
    It will parse the json data and create or replace fields in the internal data dictionary with
    the corresponding json fields.

    At the moment only flat json files can be processed correctly.

    Configuration example:

    - module: JsonParser
      configuration:
        source_field: 'data'                    # <default: 'data'; type: string; is: optional>
      receivers:
        - NextHandler
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        #BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        BaseModule.BaseModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')

    def handleEvent(self, event):
        if self.source_field not in event:
            yield event
            return
        json_string = str(event[self.source_field]).strip("'<>() ").replace('\'', '\"')
        try:
            json_data = json.loads(json_string)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not parse json data %s. Exception: %s, Error: %s." % (event, etype, evalue))
            yield event
            return
        for field_name, field_value in json_data.iteritems():
            event[field_name] = field_value
        yield event