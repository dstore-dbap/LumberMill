# -*- coding: utf-8 -*-
import os
import sys
import socket

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class StdIn(BaseThreadedModule):
    """
    Reads data from stdin and sends it to its output queues.

    Configuration template:

    - StdIn:
       multiline:                       # <default: False; type: boolean; is: optional>
       stream_end_signal:               # <default: False; type: boolean||string; is: optional>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = False

    def configure(self, configuration):
        BaseThreadedModule.configure(self, configuration)
        self.multiline = self.getConfigurationValue('multiline')
        self.stream_end_signal = self.getConfigurationValue('stream_end_signal')

    def run(self):
        if not self.receivers:
            self.logger.error("Will not start module %s since no receivers are set." % (self.__class__.__name__))
            return
        self.pid = os.getpid()
        hostname = socket.gethostname()
        multiline_data = ""
        while self.alive:
            data = sys.stdin.readline()
            if data.__len__() > 0:
                if not self.multiline:
                    self.sendEvent(Utils.getDefaultEventDict({"received_from": 'stdin://%s' % hostname, "data": data}, caller_class_name=self.__class__.__name__))
                else:
                    if self.stream_end_signal and self.stream_end_signal == data:
                        self.sendEvent(Utils.getDefaultEventDict({"received_from": 'stdin://%s' % hostname, "data": multiline_data}, caller_class_name=self.__class__.__name__))
                        multiline_data = ""
                        continue
                    multiline_data += data
            else: # an empty line means stdin has been closed
                if multiline_data.__len__() > 0:
                    self.sendEvent(Utils.getDefaultEventDict({"received_from": 'stdin://%s' % hostname, "data": multiline_data}, caller_class_name=self.__class__.__name__))
                self.lumbermill.shutDown()
                self.alive = False