import sys
import BaseModule
import simplejson as json

class JsonParser(BaseModule.BaseModule):
    
    def handleData(self, data):
        """
        This method expects json content in the internal data dictionary data field.
        It will just parse the json and create or replace fields in the internal data dictionary with
        the corresponding json fields.
        At the moment only flat json files can be processed correctly. 
        """
        try: 
            json_data = json.loads(data['data'])
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not parse json data %s. Exception: %s, Error: %s." % (data, etype, evalue))
            sys.exit(255)
        for field_name, field_value in json_data.iteritems():
            data[field_name] = field_value
        self.logger.debug("Output: %s" % data)