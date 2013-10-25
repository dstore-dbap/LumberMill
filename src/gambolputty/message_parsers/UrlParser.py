import BaseModule
import urlparse
from Decorators import GambolPuttyModule

@GambolPuttyModule
class UrlParser(BaseModule.BaseModule):
    """
    Parse and extract url parameters.

    Configuration example:

    - module: UrlParser
      configuration:
        source-field: uri       # <type: string; is: required>
    """

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        try:
            if configuration['source-field'].__len__ == 0:
                raise KeyError
        except KeyError:
            self.logger.error("source-field not set in configuration. Please set a least one field to use for parsing an url string.")
            self.shutDown()

    def handleData(self, data):
        lookup_field = self.getConfigurationValue('source-field', data)
        if lookup_field in data:
            parsed_url = urlparse.urlparse('http://www.test.de%s' % (data[lookup_field]))
            data.update(dict(urlparse.parse_qsl(parsed_url.query)))
        return data