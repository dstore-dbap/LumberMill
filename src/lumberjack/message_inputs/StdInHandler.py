import sys
import os
import select
import socket
import BaseModule
import Utils
import time

class StdInHandler(BaseModule.BaseModule):
    
    def setup(self, lj):
        self.lj = lj
        self.multiline = False
    
    def configure(self, configuration):
        if 'multiline' in configuration:
            self.multiline = configuration['multiline']
    
    def run(self):
        hostname = socket.gethostname()
        multiline_data = ""
        if not self.output_queues:
            return
        while sys.stdin in select.select([sys.stdin], [], [], 1)[0]:
            data = sys.stdin.readline()
            #print "### %s (%s)" % (data, data.__len__())
            if data.__len__() > 0:
                if not self.multiline:
                    self.addToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": data}))
                else:
                    multiline_data += data
            else: # an empty line means stdin has been closed
                if multiline_data.__len__() > 0:
                    self.addToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": multiline_data}))
                while BaseModule.BaseModule.messages_in_queues > 0:
                    time.sleep(.01)
                self.lj.shutDown()
                return