# -*- coding: utf-8 -*-
import types

from tld import get_tld

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Buffers import MemoryCache
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class DomainNameParser(BaseThreadedModule):
    r"""
    Parse fqdn to top level domain and subdomain parts.

    A string like:

        "http://some.subdomain.google.co.uk"

    will produce this dictionary:

    'domain_name_info': {  'tld': 'google.co.uk',
                           'domain': 'google',
                           'suffix': 'co.uk',
                           'subdomain': 'some.subdomain' }

    source_field: Input field to parse.
    target_field: Field to update with parsed info fields.

    Configuration template:

    - UserAgentParser:
       source_field:                    # <type: string||list; is: required>
       target_field:                    # <default: 'domain_name_info'; type:string; is: optional>
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')
        self.target_field = self.getConfigurationValue('target_field')
        self.in_mem_cache = MemoryCache(size=1000)

    def handleEvent(self, event):
        if self.source_field in event:
            # Try to get it from cache.
            try:
                domain_name_info = self.in_mem_cache.get(event[self.source_field])
            except KeyError:
                domain_name_info = get_tld(event[self.source_field], as_object=True, fail_silently=True)
                if domain_name_info:
                    self.in_mem_cache.set(event[self.source_field], domain_name_info)
            event[self.target_field] = {'tld': domain_name_info.tld,
                                        'domain': domain_name_info.domain,
                                        'suffix': domain_name_info.suffix,
                                        'subdomain': domain_name_info.subdomain}
        yield event
