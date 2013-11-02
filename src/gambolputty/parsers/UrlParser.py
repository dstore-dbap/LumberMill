# -*- coding: utf-8 -*-
import BaseThreadedModule
import urlparse
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class UrlParser(BaseThreadedModule.BaseThreadedModule):
    """
    Parse and extract url parameters.

    Configuration example:

    - module: UrlParser
      configuration:
        source_field: uri       # <type: string; is: required>
    """

    def handleData(self, data):
        lookup_field = self.getConfigurationValue('source_field', data)
        if lookup_field in data:
            parsed_url = urlparse.urlparse('http://www.test.de%s' % (data[lookup_field]))
            data.update(dict(urlparse.parse_qsl(parsed_url.query)))
        yield data