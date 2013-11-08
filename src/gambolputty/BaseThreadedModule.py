# -*- coding: utf-8 -*-
import sys
import threading
import traceback
import Utils
import BaseModule
import StatisticCollector

class BaseThreadedModule(BaseModule.BaseModule,threading.Thread):
    """
    Base class for all gambolputty modules that will run as separate threads.
    If you happen to override one of the methods defined here, be sure to know what you
    are doing ;) You have been warned ;)

    Configuration example:

    - module: SomeModuleName
      alias: AliasModuleName                    # <default: ""; type: string; is: optional>
      pool_size: 4                              # <default: 1; type: integer; is: optional>
      configuration:
        work_on_copy: True                      # <default: False; type: boolean; is: optional>
        redis_client: RedisClientName           # <default: ""; type: string; is: optional>
        redis_key: XPathParser%(server_name)s   # <default: ""; type: string; is: required if redis_client is True else optional>
        redis_ttl: 600                          # <default: 60; type: integer; is: optional>
      receivers:
       - ModuleName
       - ModuleAlias
    """

    def __init__(self, gp=False):
        BaseModule.BaseModule.__init__(self, gp)
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        if not self.input_queue:
            # Only issue warning for those modules that are expected to have an input queue.
            # TODO: A better solution should be implemented...
            if self.module_type not in ['stand_alone']:
                self.logger.warning("%sWill not start module %s since no input queue set.%s" % (Utils.AnsiColors.WARNING, self.__class__.__name__, Utils.AnsiColors.ENDC))
            return
        while self.is_alive:
            data = False
            try:
                data = self.getEventFromInputQueue()
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.logger.error("%sCould not read data from input queue.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC) )
                traceback.print_exception(exc_type, exc_value, exc_tb)
                continue
            for data in self.handleData(data):
                if data is not None:
                    self.addEventToOutputQueues(data)
                else:
                    StatisticCollector.StatisticCollector().decrementCounter('events_in_process')
