# -*- coding: utf-8 -*-
import sys
import BaseThreadedModule
import simplejson as json
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class JsonParser(BaseThreadedModule.BaseThreadedModule):
    """
    It will parse the json data and create or replace fields in the internal data dictionary with
    the corresponding json fields.

    At the moment only flat json files can be processed correctly.

    Configuration example:

    - module: JsonParser
      configuration:
        source-field: 'data'                    # <default: 'data'; type: string; is: optional>
      receivers:
        - NextHandler
    """

    def handleData(self, data):
        try:
            json_data = json.loads(self.getConfigurationValue('source-field', data))
        except:
            etype, evalue, etb = sys.exc_info()
            print "Could not parse json data %s. Exception: %s, Error: %s." % (data, etype, evalue)
            self.logger.error("Could not parse json data %s. Exception: %s, Error: %s." % (data, etype, evalue))
            return data
        for field_name, field_value in json_data.iteritems():
            data[field_name] = field_value
        return data