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

    module_type = "parser"
    """Set module type"""

    def handleData(self, event):
        lookup_field = self.getConfigurationValue('source_field', event)
        if lookup_field in event:
            parsed_url = urlparse.urlparse('http://www.test.de%s' % (event[lookup_field]))
            event.update(dict(urlparse.parse_qsl(parsed_url.query)))
        yield event