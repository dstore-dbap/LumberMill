# -*- coding: utf-8 -*-
import Utils
import BaseThreadedModule
import Decorators
import types
import dns.resolver
from dns import reversename, resolver

@Decorators.ModuleDocstringParser
class AddDnsLookup(BaseThreadedModule.BaseThreadedModule):
    """
    Add dns info for selected fields. The dns servers used are the ones configured for the system GambolPutty is
    running on.

    action: Either resolve or revers.
    source_fields: List of fields to use for (reverse) lookups. First successful lookup result will be used.
    target_field: Target field to store result of lookup. If none is provided, the source field will be replaced.
    nameservers: List of nameservers to use. If not provided, the system default servers will be used.
    timeout: Timeout for lookups in seconds.

    Configuration template:

    - AddDnsLookup:
       action:             # <default: 'resolve'; type: string; is: optional; values: ['resolve', 'reverse']>
       source_fields:      # <default: None; type: string||list; is: required>
       target_field:       # <default: None; type: None||string; is: optional>
       nameservers:        # <default: None; type: None||string||list; is: optional>
       timeout:            # <default: 1; type: integer; is: optional>
       receivers:
          - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.source_fields = self.getConfigurationValue('source_fields')
        # Allow single string as well.
        if isinstance(self.source_fields, types.StringTypes):
            self.source_fields = [self.source_fields]
        self.target_field = self.getConfigurationValue('target_field')
        self.nameservers = self.getConfigurationValue('nameservers')
        # Allow single string as well.
        if isinstance(self.nameservers, types.StringTypes):
            self.nameservers = [self.nameservers]
        self.resolver = dns.resolver.Resolver()
        if self.nameservers:
            self.resolver.nameserves = self.nameservers
        self.resolver.timeout = self.getConfigurationValue('timeout')
        self.resolver.lifetime = self.getConfigurationValue('timeout')
        # Monkeypatch the lookup method
        if self.getConfigurationValue('action') == 'resolve':
            self.doLookup = self.doNormalLookup
        else:
            self.doLookup = self.doReverseLookup

    def doLookup(self):
        return

    def doReverseLookup(self, ip_address):
        try:
            rev_name = reversename.from_address(ip_address)
            return str(resolver.query(rev_name, "PTR")[0])
        except:
            return None

    def doNormalLookup(self, hostname):
        try:
            return str(self.resolver.query(hostname)[0])
        except:
            return None

    def handleEvent(self, event):
        for source_field in self.source_fields:
            if source_field not in event:
                continue
            result = self.doLookup(event[source_field])
            if not result:
                continue
            if self.target_field:
                event[self.target_field] = result
            else:
                event[source_field] = result
        yield event