# -*- coding: utf-8 -*-
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class DevNullSink(BaseThreadedModule.BaseThreadedModule):
    """
    Just discard messeages send to this module.

    Configuration example:

    - DevNullSink
    """

    module_type = "output"
    """Set module type"""

    def handleEvent(self, event):
        event = None
        yield None