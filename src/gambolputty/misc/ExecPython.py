# -*- coding: utf-8 -*-
import pprint
import sys
import StringIO
import BaseModule
import Utils
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class ExecPython(BaseModule.BaseModule):
    """
    Execute python code.

    To make sure that the yaml parser keeps the tabs in the source code, ensure that the code is preceded by a comment.
    E.g.:

- ExecPython:
    source: |
      # Useless comment...
        try:
            imported = math
        except NameError:
            import math
        event['request_time'] = math.ceil(event['request_time'] * 1000)

    code: Code to execute.
    debug: Set to True to output the string that will be executed.

    Configuration example:

    - ExecPython:
        source:               # <type: string; is: required>
        debug:                # <default: False; type: boolean; is: optional>
    """
    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        source = "def UserFunc(event):\n%s" % self.getConfigurationValue("source")
        if self.getConfigurationValue("debug"):
            print source
        exec(source)
        try:
            pass
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sExecPython failed while creating user function. Exception: %s, Error: %s%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))
            self.gp.shutDown()
        self._func = locals()["UserFunc"]


    def handleEvent(self, event):
        try:
            self._func(event)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("%sExecPython failed. Exception: %s, Error: %s%s" % (Utils.AnsiColors.WARNING, etype, evalue, Utils.AnsiColors.ENDC))
        yield event
