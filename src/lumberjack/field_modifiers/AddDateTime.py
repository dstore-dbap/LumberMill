import datetime
import BaseModule

class AddDateTime(BaseModule.BaseModule):
    """Add a field with the current datetime.
    Configuration example:

    - module: AddDateTime
      configuration:
        field: 'my_timestamp'
        format: '%Y-%M-%dT%H:%M:%S'
    """

    def setup(self):
        # Set defaults
        self.fieldname = '@timestamp'
        self.datetime_format = '%Y-%m-%dT%H:%M:%S'

    def configure(self, configuration):
        # Call parent configure method
        super(AddDateTime, self).configure(configuration)
        if 'field' in configuration:
            self.fieldname = configuration['field']
        if 'format' in configuration:
            self.datetime_format = configuration['format']

    def handleData(self, data):
        data[self.fieldname] = datetime.datetime.utcnow().strftime(self.datetime_format)
        return data