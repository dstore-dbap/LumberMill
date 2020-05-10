# -*- coding: utf-8 -*-
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class DevNull(BaseThreadedModule):
    """
    Just discard messages send to this module.

    Configuration template:

    - output.DevNull
    """

    module_type = "output"
    """Set module type"""

    def handleEvent(self, event):
        yield None
