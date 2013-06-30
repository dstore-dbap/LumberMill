import time
import BaseModule

class AddTimeStamp(BaseModule.BaseModule):

    def handleData(self, data):
        data['timestamp'] = int(time.time())
        return data