# -*- coding: utf-8 -*-
import re
import sys

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser, setInterval
from lumbermill.utils.misc import TimedFunctionManager


@ModuleDocstringParser
class Math(BaseThreadedModule):
    """
    Execute arbitrary math functions.

    Simple example to cast nginx request time (seconds with milliseconds as float) to apache request time
    (microseconds as int):

    - Math:
        filter: if $(server_type) == "nginx"
        target_field: request_time
        function: int(float($(request_time)) * 1000)

    If interval is set, the results of <function> will be collected for the interval time and the final result
    will be calculated via the <results_function>.

    function: the function to be applied to/with the event data.
    results_function: if interval is configured, use this function to calculate the final result.
    interval: Number of seconds to until.
    target_field: event field to store the result in.

    Configuration template:

    - Math:
       function:                        # <type: string; is: required>
       results_function:                # <default: None; type: None||string; is: optional if interval is None else required>
       interval:                        # <default: None; type: None||float||integer; is: optional>
       target_field:                    # <default: None; type: None||string; is: optional>
       receivers:
        - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.results = []
        function_str = "lambda event: " + re.sub('%\((.*?)\)s', r"event.get('\1', False)", self.getConfigurationValue('function'))
        self.function = self.compileFunction(function_str)
        if self.getConfigurationValue('results_function'):
            function_str = "lambda results: "+ re.sub('%\((.*?)\)s', r"results", self.getConfigurationValue('results_function'))
            self.results_function = self.compileFunction(function_str)
        self.target_field = self.getConfigurationValue('target_field')
        self.interval = self.getConfigurationValue('interval')

    def compileFunction(self, function_str):
        try:
            lambda_function = eval(function_str)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Failed to compile function: %s. Exception: %s, Error: %s." % (function_str, etype, evalue))
            self.lumbermill.shutDown()
        return lambda_function

    def getEvaluateFunc(self):
        @setInterval(self.interval)
        def timedEvaluateFacets():
            if self.results:
                self.evaluateResults()
        return timedEvaluateFacets

    def initAfterFork(self):
        if self.interval:
            self.evaluate_facet_data_func = self.getEvaluateFunc()
            self.timed_func_handler = TimedFunctionManager.startTimedFunction(self.evaluate_facet_data_func)
        BaseThreadedModule.initAfterFork(self)

    def evaluateResults(self):
        results = self.results
        self.results = []
        try:
            result = self.results_function(results)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Failed to evaluate result function %s. Exception: %s, Error: %s." % (self.getConfigurationValue('results_function'), etype, evalue))
            return
        if self.target_field:
            event_dict = {self.target_field: result}
        else:
            event_dict = {'math_result': result}
        event = DictUtils.getDefaultEventDict(event_dict, caller_class_name=self.__class__.__name__, event_type='math')
        self.sendEvent(event)

    def handleEvent(self, event):
        try:
            result = self.function(event)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Failed to evaluate function %s. Exception: %s, Error: %s." % (self.getConfigurationValue('function'), etype, evalue))
        if self.interval:
            self.results.append(result)
        elif self.target_field:
            event[self.target_field] = result
        yield event