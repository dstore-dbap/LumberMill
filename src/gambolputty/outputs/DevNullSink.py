# -*- coding: utf-8 -*-
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class DevNullSink(BaseThreadedModule.BaseThreadedModule):
    """
    Just discard messeages send to this module.BaseThreadedModule

    Configuration example:

    - module: DevNullSink
    """
    def handleData(self, event):
        yield