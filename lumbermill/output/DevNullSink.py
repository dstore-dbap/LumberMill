# -*- coding: utf-8 -*-
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class DevNullSink(BaseThreadedModule):
    """
    Just discard messeages send to this module.

    Configuration template:

    - DevNullSink
    """

    module_type = "output"
    """Set module type"""

    def handleEvent(self, event):
        yield None