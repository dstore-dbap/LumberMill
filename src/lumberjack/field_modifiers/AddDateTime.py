import isodate
import datetime
import BaseModule

class AddDateTime(BaseModule.BaseModule):

    def configure(self, configuration):
        # Set defaults
        self.fieldname = configuration['field'] if 'field' in configuration else '@timestamp'

    def handleData(self, data):
        data[self.fieldname] = isodate.datetime_isoformat(datetime.datetime.utcnow())
        return data