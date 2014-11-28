# -*- coding: utf-8 -*-
import BaseThreadedModule
import Decorators

@Decorators.ModuleDocstringParser
class DevNullSink(BaseThreadedModule.BaseThreadedModule):
    """
    Just discard messeages send to this module.

    Configuration template:

    - DevNullSink
    """

    module_type = "output"
    """Set module type"""

    def handleEvent(self, event):
        yield None