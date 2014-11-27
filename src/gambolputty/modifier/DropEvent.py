# -*- coding: utf-8 -*-
import Utils
import BaseThreadedModule
import Decorators


@Decorators.ModuleDocstringParser
class DropEvent(BaseThreadedModule.BaseThreadedModule):
    """
    Drop all events received by this module.

    This module is intended to be used with an activated filter.

    Configuration template:

    - DropEvent:
        receivers:
          - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def handleEvent(self, event):
        yield None