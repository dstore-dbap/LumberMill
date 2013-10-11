import sys
import os
import select
import socket
import BaseModule
import Utils
import time

class StdInHandler(BaseModule.BaseModule):
    """Reads data from stdin and sends it to its output queue

    Configuration example:

    - module: StdInHandler
      configuration:
        multiline: True
        stream_end_signal: #########
        stream_end_signal: #########
    """
    def setup(self):
        # Call parent setup method
        super(StdInHandler, self).setup()
        # Set defaults
        self.multiline = False
        self.stream_end_signal = False
    
    def configure(self, configuration):
        if 'multiline' in configuration:
            self.multiline = configuration['multiline']
        if 'stream_end_signal' in configuration:
            self.stream_end_signal = configuration['stream_end_signal']
            
    def run(self, input=sys.stdin):
        hostname = socket.gethostname()
        multiline_data = ""
        if not self.output_queues:
            return
        #while input in select.select([input], [], [], 1)[0]:
        while True:
            data = input.readline()
            if data.__len__() > 0:
                if not self.multiline:
                    self.addToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": data}))
                else:
                    if self.stream_end_signal and self.stream_end_signal == data:
                        self.addToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": multiline_data}))
                        multiline_data = ""
                        continue
                    multiline_data += data
            else: # an empty line means stdin has been closed
                if multiline_data.__len__() > 0:
                    self.addToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": multiline_data}))
                while self.isAlive() and BaseModule.BaseModule.messages_in_queues > 0:
                    time.sleep(.01)
                self.lj.shutDown()
                return