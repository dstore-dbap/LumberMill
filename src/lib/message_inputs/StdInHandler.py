import sys
import select
import socket
import BaseModule
import Utils

class StdInHandler(BaseModule.BaseModule):
    
    def run(self):
        hostname = socket.gethostname()
        while sys.stdin in select.select([sys.stdin], [], [], 1)[0]:
            data = sys.stdin.readline()
            if data.__len__() > 0 and self.output_queues:
                self.addToOutputQueues(Utils.getDefaultDataDict({"received_from": 'stdin', "data": data}))
            else: # an empty line means stdin has been closed
                sys.exit(0)