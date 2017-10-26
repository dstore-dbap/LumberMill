# -*- coding: utf-8 -*-

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class Noop(BaseThreadedModule):
    """
    Just do nothing ;)

    Useful only for testing purposes or if you just want to use input/output filter or add/delete field.

    Configuration template:

    - Noop:
       receivers:
        - NextModule
    """

    module_type = "misc"
    """Set module type"""

    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        @return data: dictionary
        """
        yield event