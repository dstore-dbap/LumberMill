# -*- coding: utf-8 -*-
import Queue
import Utils
import BaseThreadedModule
import threading
import Decorators
import types
import socket


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
        self.in_mem_cache = Utils.MemoryCache(size=5000)
        self.source_fields = self.getConfigurationValue('source_fields')
        # Allow single string as well.
        if isinstance(self.source_fields, types.StringTypes):
            self.source_fields = [self.source_fields]
        self.target_field = self.getConfigurationValue('target_field')
        self.nameservers = self.getConfigurationValue('nameservers')
        # Allow single string as well.
        if isinstance(self.nameservers, types.StringTypes):
            self.nameservers = [self.nameservers]
        self.lookup_type = self.getConfigurationValue('action')
        self.lookup_threads_pool_size = 3

    def initAfterFork(self):
        self.queue = Queue.Queue(20)
        self.lookup_threads = [LookupThread(self.queue, self.lookup_type, self) for _ in range(0, self.lookup_threads_pool_size)]
        for thread in self.lookup_threads:
            thread.start()
        BaseThreadedModule.BaseThreadedModule.initAfterFork(self)

    def handleEvent(self, event):
        for source_field in self.source_fields:
            if source_field not in event:
                continue
            target_field = self.target_field if self.target_field else source_field
            self.queue.put({'source_field': source_field,
                            'target_field': target_field,
                            'event': event})
        yield None

    def shutDown(self):
        BaseThreadedModule.BaseThreadedModule.shutDown(self)
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
            rev_name = socket.gethostbyaddr(ip_address)[0]
        except:
            rev_name = None
        #if (time.time() - started) > .1:
        #    print("Reverse lookup of %s(%s) took %s." % (ip_address, rev_name, time.time() - started))
        return rev_name

    def doLookup(self, host_name):
        try:
            ip_address = socket.gethostbyname(host_name)
        except:
            ip_address = None
        return ip_address