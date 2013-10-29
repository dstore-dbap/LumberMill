# -*- coding: utf-8 -*-
import BaseModule

class DevNullSink(BaseModule.BaseModule):
    """
    Just discard messeages send to this module.BaseModule

    Configuration example:

    - module: DevNullSink
    """
    def handleData(self, data):
        return False