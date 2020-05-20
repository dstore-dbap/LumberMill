# -*- coding: utf-8 -*-
import sys

from kafka import KafkaConsumer

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class Kafka(BaseThreadedModule):
    """
    Simple kafka input.


    Configuration template:

    - input.Kafka:
       topic:                           # <type: string; is: required>
       brokers:                         # <default: ['localhost:9092']; type: list; is: optional>
       client_id:                       # <default: 'kafka.consumer.kafka'; type: string; is: optional>
       group_id:                        # <default: None; type: None||string; is: optional>
       fetch_min_bytes:                 # <default: 1; type: integer; is: optional>
       auto_offset_reset:               # <default: 'latest'; type: string; is: optional>
       enable_auto_commit:              # <default: False; type: boolean; is: optional>
       auto_commit_interval_ms:         # <default: 60000; type: integer; is: optional>
       consumer_timeout_ms:             # <default: -1; type: integer; is: optional>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
        # Call parent configure method.
        BaseThreadedModule.configure(self, configuration)
        self.enable_auto_commit = self.getConfigurationValue('enable_auto_commit')

    def initAfterFork(self):
        try:
            self.consumer = KafkaConsumer(self.getConfigurationValue('topic'),
                                          bootstrap_servers=self.getConfigurationValue('brokers'),
                                          client_id=self.getConfigurationValue('client_id'),
                                          group_id=self.getConfigurationValue('group_id'),
                                          fetch_min_bytes=self.getConfigurationValue('fetch_min_bytes'),
                                          auto_offset_reset=self.getConfigurationValue('auto_offset_reset'),
                                          enable_auto_commit=self.getConfigurationValue('enable_auto_commit'),
                                          auto_commit_interval_ms=self.getConfigurationValue('auto_commit_interval_ms'),
                                          consumer_timeout_ms=self.getConfigurationValue('consumer_timeout_ms')
                                          )
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not create kafka consumer. Exception: %s, Error: %s." % ( etype, evalue))
            self.lumbermill.shutDown()

    def run(self):
        while self.alive:
            for kafka_event in self.consumer:
                pprint.pprint(kafka_event)
                event = DictUtils.getDefaultEventDict(dict={"topic": kafka_event.topic, "data": kafka_event.value}, caller_class_name=self.__class__.__name__)
                self.sendEvent(event)
                if(self.enable_auto_commit):
                    self.consumer.task_done(kafka_event)
