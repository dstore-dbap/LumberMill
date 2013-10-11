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
        """
        Setup method to set default values.
        This method will be called by the LumberJack main class after initializing the module
        and before the configure method of the module is called.
        """
        # Call parent setup method
        super(AddDateTime, self).setup()
        self.fieldname = '@timestamp'
        self.datetime_format = '%Y-%m-%dT%H:%M:%S'

    def configure(self, configuration):
        """
        Configure the module.
        This method will be called by the LumberJack main class after initializing the module
        and after the configure method of the module is called.
        The configuration parameter contains k:v pairs of the yaml configuration for this module.

        @param configuration: dictionary
        @return:
        """
        # Call parent configure method
        super(AddDateTime, self).configure(configuration)
        if 'field' in configuration:
            self.fieldname = configuration['field']
        if 'format' in configuration:
            self.datetime_format = configuration['format']

    def handleData(self, data):
        """
        Process the event.

        @param data: dictionary
        @return data: dictionary
        """
        data[self.fieldname] = datetime.datetime.utcnow().strftime(self.datetime_format)
        return data