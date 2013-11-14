# -*- coding: utf-8 -*-
import Utils
import BaseThreadedModule
import BaseMultiProcessModule
import time
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class Spam(BaseThreadedModule.BaseThreadedModule):
    """
    Emits events as fast as possible.

    Use this module to load test GambolPutty.

    Configuration example:

    - module: Spam
      configuration:
        event: {'Lobster': 'Thermidor', 'Truffle': 'Pate'}  # <default: {}; type: dict; is: optional>
        sleep: 0                                            # <default: 0; type: int||float; is: optional>
      receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""

    def run(self):
        while self.is_alive:
            event = Utils.getDefaultDataDict(self.getConfigurationValue("event"))
            event['timestamp'] = 10
            self.addEventToOutputQueues(event, update_counter=False)
            if self.getConfigurationValue("sleep"):
                time.sleep(self.getConfigurationValue("sleep"))