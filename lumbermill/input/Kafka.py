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

    - Kafka:
       brokers:                         # <type: list; is: required>
       topics:                          # <type: string||list; is: required>
       client_id:                       # <default: 'kafka.consumer.kafka'; type: string; is: optional>
       group_id:                        # <default: None; type: None||string; is: optional>
       fetch_message_max_bytes:         # <default: 1048576; type: integer; is: optional>
       fetch_min_bytes:                 # <default: 1; type: integer; is: optional>
       fetch_wait_max_ms:               # <default: 100; type: integer; is: optional>
       refresh_leader_backoff_ms:       # <default: 200; type: integer; is: optional>
       socket_timeout_ms:               # <default: 10000; type: integer; is: optional>
       auto_offset_reset:               # <default: 'largest'; type: string; is: optional>
       auto_commit_enable:              # <default: False; type: boolean; is: optional>
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
        self.auto_commit_enable = self.getConfigurationValue('auto_commit_enable')

    def initAfterFork(self):
        try:
            self.consumer = KafkaConsumer(self.getConfigurationValue('topics'),
                                          client_id=self.getConfigurationValue('client_id'),
                                          group_id=self.getConfigurationValue('group_id'),
                                          fetch_message_max_bytes=self.getConfigurationValue('fetch_message_max_bytes'),
                                          fetch_min_bytes=self.getConfigurationValue('fetch_min_bytes'),
                                          fetch_wait_max_ms=self.getConfigurationValue('fetch_wait_max_ms'),
                                          refresh_leader_backoff_ms=self.getConfigurationValue('refresh_leader_backoff_ms'),
                                          metadata_broker_list=self.getConfigurationValue('brokers'),
                                          socket_timeout_ms=self.getConfigurationValue('socket_timeout_ms'),
                                          auto_offset_reset=self.getConfigurationValue('auto_offset_reset'),
                                          auto_commit_enable=self.getConfigurationValue('auto_commit_enable'),
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
                event = DictUtils.getDefaultEventDict(dict={"topic": kafka_event.topic, "data": kafka_event.value}, caller_class_name=self.__class__.__name__)
                self.sendEvent(event)
                if(self.auto_commit_enable):
                    self.consumer.task_done(kafka_event)
