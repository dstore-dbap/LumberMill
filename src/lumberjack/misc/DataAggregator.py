import time
import BaseModule

class DataAggregator(BaseModule.BaseModule):
    """Collect a configurable amount of messages and the pass them all to the configured receivers.

    Configuration example:

    - module: DataAggregator
      configuration:
        send_data_interval: 25
    """

    def setup(self):
        self.data_container = []
    
    def handleData(self, data):
        self.data_container.append(data)
        if len(self.data_container) < self.config['send_data_interval']:
            return
        self.logger.debug("Sending data: %s " % self.data_container)
        self.addToOutputQueues(self.data_container)
        self.data_container = []
