# -*- coding: utf-8 -*-
import datetime
import BaseModule
from Decorators import GambolPuttyModule

@GambolPuttyModule
class AddDateTime(BaseModule.BaseModule):
    """
    Add a field with the current datetime.

    Configuration example:

    - module: AddDateTime
      configuration:
        target-field: 'my_timestamp' # <default: '@timestamp'; type: string; is: optional>
        format: '%Y-%M-%dT%H:%M:%S'  # <default: '%Y-%m-%dT%H:%M:%S'; type: string; is: optional>
    """

    def handleData(self, data):
        """
        Process the event.

        @param data: dictionary
        @return data: dictionary
        """
        data[self.getConfigurationValue('target-field', data)] = datetime.datetime.utcnow().strftime(self.getConfigurationValue('format', data))
        return data