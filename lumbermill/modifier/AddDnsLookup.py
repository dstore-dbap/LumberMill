# -*- coding: utf-8 -*-
import Queue
import threading
import types
from dns import resolver, reversename

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class AddDnsLookup(BaseThreadedModule):
    """
    Add dns info for selected fields. The dns servers used are the ones configured for the system LumberMill is
    running on.

    action: Either resolve or revers.
    source_field: Source field to use for (reverse) lookups.
    target_field: Target field to store result of lookup. If none is provided, the source field will be replaced.
    nameservers: List of nameservers to use. If not provided, the system default servers will be used.
    timeout: Timeout for lookups in seconds.

    Configuration template:

    - AddDnsLookup:
       action:                          # <default: 'resolve'; type: string; is: optional; values: ['resolve', 'reverse']>
       source_field:                    # <default: None; type: string; is: required>
       target_field:                    # <default: None; type: None||string; is: optional>
       nameservers:                     # <default: None; type: None||string||list; is: optional>
       timeout:                         # <default: 1; type: integer; is: optional>
       receivers:
          - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.in_mem_cache = Utils.MemoryCache(size=5000)
        self.lookup_type = self.getConfigurationValue('action')
        self.source_field = self.getConfigurationValue('source_field')
        self.target_field = self.getConfigurationValue('target_field')
        self.nameservers = self.getConfigurationValue('nameservers')
        self.timeout = self.getConfigurationValue('timeout')
        # Allow single string as well.
        if isinstance(self.nameservers, types.StringTypes):
            self.nameservers = [self.nameservers]
        self.lookup_threads_pool_size = 3

    def initAfterFork(self):
        self.resolver = resolver.Resolver()
        self.resolver.timeout = self.timeout
        self.resolver.lifetime = self.timeout
        if self.nameservers:
            self.resolver.nameservers = self.nameservers
        self.queue = Queue.Queue(20)
        self.lookup_threads = [LookupThread(self.queue, self.lookup_type, self) for _ in range(0, self.lookup_threads_pool_size)]
        for thread in self.lookup_threads:
            thread.start()
        BaseThreadedModule.initAfterFork(self)

    def handleEvent(self, event):
        if self.source_field in event:
            target_field = self.target_field if self.target_field else self.source_field
            self.queue.put({'source_field': self.source_field,
                            'target_field': target_field,
                            'event': event})
        yield None

    def shutDown(self):
        BaseThreadedModule.shutDown(self)
        for thread in self.lookup_threads:
            thread.stop()
            thread.join()

class LookupThread(threading.Thread):
    def __init__(self, queue, lookup_type, caller):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lookup_type = lookup_type
        self.caller = caller
        self.daemon = True
        self.alive = True

    def stop(self):
        self.alive = False

    def run(self):
        while self.alive:
            try:
                payload = self.queue.get()
            except Queue.Empty:
                continue
            source_field = payload['source_field']
            target_field = payload['target_field']
            event = payload['event']
            host_or_ip = event[source_field]
            # Try to get it from cache.
            try:
                result = self.caller.in_mem_cache.get(host_or_ip)
            except KeyError:
                if self.lookup_type == 'resolve':
                    result = self.doLookup(host_or_ip)
                elif self.lookup_type == 'reverse':
                    result = self.doReverseLookup(host_or_ip)
            self.caller.in_mem_cache.set(host_or_ip, result)
            event[target_field] = result
            self.caller.sendEvent(event)

    def doReverseLookup(self, ip_address):
        #started = time.time()
        try:
            hostname = str(self.caller.resolver.query(reversename.from_address(ip_address), "PTR")[0])
        except:
            hostname = None
        #if (time.time() - started) > 1:
        #    print("Reverse lookup of %s(%s) took %s." % (ip_address, hostname, time.time() - started))
        return hostname

    def doLookup(self, hostname):
        try:
            ip_address = str(self.caller.resolver.query(hostname)[0])
        except:
            ip_address = None
        return ip_address