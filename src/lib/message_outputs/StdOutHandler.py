import BaseModule

class StdOutHandler(BaseModule.BaseModule):
 
    def handleData(self, data):
          print "%s" % data
