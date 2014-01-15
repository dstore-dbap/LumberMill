# -*- coding: utf-8 -*-
import sys
import BaseModule
from Decorators import ModuleDocstringParser
json = False
for module_name in ['yajl', 'simplejson', 'json']:
    try:
        json = __import__(module_name)
        print "Using %s" % module_name
        break
    except ImportError:
        pass
if not json:
    raise ImportError

@ModuleDocstringParser
class JsonParser(BaseModule.BaseModule):
    """
    It will parse the json data and create or replace fields in the internal data dictionary with
    the corresponding json fields.

    At the moment only flat json files can be processed correctly.

    Configuration example:

    - module: JsonParser
       source_field: 'data'                    # <default: 'data'; type: string; is: optional>
      keep_original: True                     # <default: False; type: boolean; is: optional>
      receivers:
        - NextHandler
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')
        self.drop_original = not self.getConfigurationValue('keep_original')

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
        if self.drop_original:
            event.pop(self.source_field, None)
        event.update(json_data)
        yield event