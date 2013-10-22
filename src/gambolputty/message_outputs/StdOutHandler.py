import BaseModule
import pprint

class StdOutHandler(BaseModule.BaseModule):

    def handleData(self, data):
        if 'pretty-print' in self.configuration_data and self.configuration_data['pretty-print'] == True:
            pprint.pprint(data)
        else:
            print "%s" % data
