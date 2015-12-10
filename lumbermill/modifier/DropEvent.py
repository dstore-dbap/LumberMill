# -*- coding: utf-8 -*-
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class DropEvent(BaseThreadedModule):
    """
    Drop all events received by this module.

    This module is intended to be used with an activated filter.

    Configuration template:

    - DropEvent
    """

    module_type = "modifier"
    """Set module type"""

    def handleEvent(self, event):
        yield None