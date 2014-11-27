# -*- coding: utf-8 -*-
import Utils
import BaseThreadedModule
import Decorators
import re
import sys

@Decorators.ModuleDocstringParser
class Math(BaseThreadedModule.BaseThreadedModule):
    """
    Execute arbitrary math functions.

    If interval is set, the math function

    function:
    interval: Number of seconds to until.
    backend: Name of a key::value store plugin. When running multiple instances of gp this backend can be used to
             synchronize events across multiple instances.
    backend_ttl: Time to live for backend entries. Should be greater than interval.

    Configuration template:

    - Math:
        function:                   # <type: string; is: required>
        results_function:           # <default: None; type: None||string; is: optional if interval is None else required>
        target_field:               # <default: None; type: None||string; is: optional>
        interval:                   # <default: None; type: None||float||integer; is: optional>
        backend:                    # <default: None; type: None||string; is: optional>
        backend_ttl:                # <default: 60; type: integer; is: optional>
        receivers:
          - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.results = []
        function_str = "lambda event: " + re.sub('%\((.*?)\)s', r"event.get('\1', False)", self.getConfigurationValue('function'))
        self.function = self.compileFunction(function_str)
        if self.getConfigurationValue('results_function'):
            function_str = "lambda results: "+ re.sub('%\((.*?)\)s', r"results", self.getConfigurationValue('results_function'))
            self.results_function = self.compileFunction(function_str)
        self.target_field = self.getConfigurationValue('target_field')
        self.interval = self.getConfigurationValue('interval')
        self.backend_ttl = self.getConfigurationValue('backend_ttl')
        self.persistence_backend = None
        if self.getConfigurationValue('backend'):
            backend_info = self.gp.getModuleInfoById(self.getConfigurationValue('backend'))
            if not backend_info:
                self.logger.error("Could not find %s backend for persistant storage." % (self.getConfigurationValue('backend')))
                self.gp.shutDown()
                return
            self.persistence_backend = backend_info['instances'][0]

    def compileFunction(self, function_str):
        try:
            lambda_function = eval(function_str)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Failed to compile function: %s. Exception: %s, Error: %s." % (function_str, etype, evalue))
            self.gp.shutDown()
        return lambda_function

    def getEvaluateFunc(self):
        @Decorators.setInterval(self.interval)
        def timedEvaluateFacets():
            if self.results:
                self.evaluateResults()
        return timedEvaluateFacets

    def prepareRun(self):
        if self.interval:
            self.evaluate_facet_data_func = self.getEvaluateFunc()
            self.timed_func_handler_a = Utils.TimedFunctionManager.startTimedFunction(self.evaluate_facet_data_func)
        if self.persistence_backend:
            self.store_facets_in_backend_func = self.getStoreFunc()
            self.timed_func_handler_b = Utils.TimedFunctionManager.startTimedFunction(self.store_facets_in_backend_func)
        BaseThreadedModule.BaseThreadedModule.prepareRun(self)

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
        event = Utils.getDefaultEventDict(event_dict, caller_class_name=self.__class__.__name__, event_type='math')
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