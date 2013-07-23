import BaseModule
import pprint
import time

class StdOutHandler(BaseModule.BaseModule):

    def handleData(self, data):
        if 'pretty-print' in self.config and self.config['pretty-print'] == True:
            pprint.pprint(data)
        else:
            print "%s" % data
