# -*- coding: utf-8 -*-
import sys
import socket
import Utils
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class StdInHandler(BaseThreadedModule.BaseThreadedModule):
    """
    Reads data from stdin and sends it to its output queues.

    Configuration example:

    - module: StdInHandler
      configuration:
        multiline: True                  # <default: False; type: boolean; is: optional>
        stream_end_signal: #########     # <default: False; type: boolean||string; is: optional>
      receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""

    def configure(self, configuration):
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.multiline = self.getConfigurationValue('multiline')
        self.stream_end_signal = self.getConfigurationValue('stream_end_signal')

    def run(self, input=sys.stdin):
        hostname = socket.gethostname()
        multiline_data = ""
        if not self.output_queues:
            return
        while self.is_alive:
            data = input.readline()
            if data.__len__() > 0:
                if not self.multiline:
                    self.addEventToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": data}), update_counter=False) # , update_counter=False
                else:
                    if self.stream_end_signal and self.stream_end_signal == data:
                        self.addEventToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": multiline_data}), update_counter=False)
                        multiline_data = ""
                        continue
                    multiline_data += data
            else: # an empty line means stdin has been closed
                if multiline_data.__len__() > 0:
                    self.addEventToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": multiline_data}), update_counter=False)
                self.gp.shutDown()
                self.is_alive = False