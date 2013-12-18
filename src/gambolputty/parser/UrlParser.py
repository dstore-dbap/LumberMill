# -*- coding: utf-8 -*-
import BaseModule
import urlparse
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class UrlParser(BaseModule.BaseModule):
    """
    Parse and extract url parameters.

    Configuration example:

    - module: UrlParser
      configuration:
        source_field: uri       # <type: string; is: required>
    """

    module_type = "parser"
    """Set module type"""

    def handleEvent(self, event):
        lookup_field = self.getConfigurationValue('source_field', event)
        if lookup_field in event:
            parsed_url = urlparse.urlparse('http://www.test.de%s' % (event[lookup_field]))
            event.update(dict(urlparse.parse_qsl(parsed_url.query)))
        self.sendEventToReceivers(event)