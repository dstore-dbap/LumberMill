# -*- coding: utf-8 -*-
import BaseModule

class DevNullSink(BaseModule.BaseModule):
    
    def handleData(self, data):
        return False