import sys
import os
import select
import socket
import BaseModule
import Utils
import time

class StdInHandler(BaseModule.BaseModule):
    
    def run(self):
        hostname = socket.gethostname()
        while sys.stdin in select.select([sys.stdin], [], [], 1)[0]:
            data = sys.stdin.readline()
            if data.__len__() > 0 and self.output_queues:
                self.addToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin://%s' % hostname, "data": data}))
            else: # an empty line means stdin has been closed
                while BaseModule.BaseModule.messages_in_queues > 0:
                    time.sleep(.1)
                self.lj.shutDown()