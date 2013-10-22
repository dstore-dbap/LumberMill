import BaseModule
import urlparse

class UrlParser(BaseModule.BaseModule):
    """Parse and extract url parameters

    - ModuleContainer:
        filter-by-marker: match
    """

    def configure(self, configuration):
        # Call parent configure method
        super(UrlParser, self).configure(configuration)
        try:
            if configuration['source-fields'].__len__ == 0:
                raise KeyError
        except KeyError:
            self.logger.error("lookup_fields not set in configuration. Please set a least one field to use for parsing an url string.")
            self.shutDown()

    def handleData(self, data):
        for lookup_field in self.getConfigurationValue('source-fields', data):
            if lookup_field not in data:
                continue
            parsed_url = urlparse.urlparse('http://www.test.de%s' % (data[lookup_field]))
            data.update(dict(urlparse.parse_qsl(parsed_url.query)))
        return data