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
            self.lookup_fields = configuration['lookup_fields']
            if self.lookup_fields.__len__ == 0:
                raise KeyError
        except KeyError:
            self.logger.error("lookup_fields not set in configuration. Please set a least one field to use for parsing an url string.")
            self.lj.shutDown()

    def handleData(self, data):
        for lookup_field in self.lookup_fields:
            if lookup_field not in data:
                continue
            parsed_url = urlparse.urlparse(u'http://www.test.de%s' % (data[lookup_field].encode('utf8')))
            #new_data = urlparse.parse_qs(parsed_url.query)
            #new_data['message_type'] = data['message_type']
            #new_data['data'] = data['data']
            #new_data['@timestamp'] = data['@timestamp']
            data.update(urlparse.parse_qs(parsed_url.query))
            return data