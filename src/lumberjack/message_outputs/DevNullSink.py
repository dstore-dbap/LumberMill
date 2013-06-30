import BaseModule

class DevNullSink(BaseModule.BaseModule):
    
    def handleData(self, data):
        return False