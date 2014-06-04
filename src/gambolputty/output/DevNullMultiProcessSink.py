# -*- coding: utf-8 -*-
import BaseMultiProcessModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class DevNullMultiProcessSink(BaseMultiProcessModule.BaseMultiProcessModule):
    """
    Just discard messeages send to this module.BaseThreadedModule

    Configuration example:

    - DevNullSink
    """

    module_type = "output"
    """Set module type"""

    def handleEvent(self, event):
        event = None
        yield None