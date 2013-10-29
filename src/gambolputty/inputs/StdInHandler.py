# -*- coding: utf-8 -*-
import sys
import socket
import Utils
import time
import BaseModule
import BaseQueue
from Decorators import GambolPuttyModule

@GambolPuttyModule
class StdInHandler(BaseModule.BaseModule):
    """
    Reads data from stdin and sends it to its output queue.

    Configuration example:

    - module: StdInHandler
      configuration:
        multiline: True                  # <default: False; type: boolean; is: optional>
        stream-end-signal: #########     # <default: False; type: string; is: optional>
    """

    module_type = "input"
    """Set module type"""

    def configure(self, configuration):
        BaseModule.BaseModule.configure(self, configuration)
        self.multiline = self.getConfigurationValue('multiline')
        self.stream_end_signal = self.getConfigurationValue('stream-end-signal')
            
    def run(self, input=sys.stdin):
        hostname = socket.gethostname()
        multiline_data = ""
        if not self.output_queues:
            return
        while True:
            data = input.readline()
            if data.__len__() > 0:
                if not self.multiline:
                    self.addEventToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": data}))
                else:
                    if self.stream_end_signal and self.stream_end_signal == data:
                        self.addEventToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": multiline_data}))
                        multiline_data = ""
                        continue
                    multiline_data += data
            else: # an empty line means stdin has been closed
                if multiline_data.__len__() > 0:
                    self.addEventToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": multiline_data}))
                self.gp.shutDown()
                return