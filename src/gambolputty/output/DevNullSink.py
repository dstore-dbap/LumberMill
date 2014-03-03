# -*- coding: utf-8 -*-
import BaseModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class DevNullSink(BaseModule.BaseModule):
    """
    Just discard messeages send to this module.BaseThreadedModule

    Configuration example:

    - DevNullSink
    """

    module_type = "output"
    """Set module type"""
