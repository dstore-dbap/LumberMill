# -*- coding: utf-8 -*-
import sys
import logging
import kafka 

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser
from lumbermill.constants import MY_HOSTNAME


@ModuleDocstringParser
class Kafka(BaseThreadedModule):
    """
    Simple kafka input.


    Configuration template:

    - input.Kafka:
       topic:                           # <type: string; is: required>
       brokers:                         # <default: ['localhost:9092']; type: list; is: optional>
       client_id:                       # <default: 'kafka.consumer.kafka'; type: string; is: optional>
       group_id:                        # <default: 'lumbermill.MY_HOSTNAME'; type: string; is: optional>
       fetch_min_bytes:                 # <default: 1; type: integer; is: optional>
       auto_offset_reset:               # <default: 'latest'; type: string; is: optional>
       enable_auto_commit:              # <default: False; type: boolean; is: optional>
       auto_commit_interval_ms:         # <default: 60000; type: integer; is: optional>
       consumer_timeout_ms:             # <default: -1; type: integer; is: optional>
       messages_to_read:                # <default: 0; type: integer; is: optional>
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
        self.group_id = self.getConfigurationValue('group_id')
        self.messages_to_read = self.getConfigurationValue('messages_to_read')
        self.message_counter = 0;
        if 'MY_HOSTNAME' in self.group_id:
            self.group_id = 'lumbermill.{}'.format(MY_HOSTNAME)
        # Set log level for kafka library if configured to other than default.
        if self.getConfigurationValue('log_level') != 'info':
            logging.getLogger('kafka').setLevel(self.logger.level)
        else:
            logging.getLogger('kafka').setLevel(logging.WARN)

    def getStartMessage(self):
        start_msg = "subscribed to %s:%s - group: %s" % (self.getConfigurationValue('brokers'), self.getConfigurationValue('topic'), self.group_id)
        return start_msg

    def initAfterFork(self):
        try:
            self.consumer = kafka.KafkaConsumer(self.getConfigurationValue('topic'),
                                                bootstrap_servers=self.getConfigurationValue('brokers'),
                                                client_id=self.getConfigurationValue('client_id'),
                                                group_id= self.group_id,
                                                fetch_min_bytes=self.getConfigurationValue('fetch_min_bytes'),
                                                auto_offset_reset=self.getConfigurationValue('auto_offset_reset'),
                                                enable_auto_commit=self.getConfigurationValue('enable_auto_commit'),
                                                auto_commit_interval_ms=self.getConfigurationValue('auto_commit_interval_ms'),
                                                consumer_timeout_ms=self.getConfigurationValue('consumer_timeout_ms'))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not create kafka consumer. Exception: %s, Error: %s." % ( etype, evalue))
            self.lumbermill.shutDown()

    def run(self):
        while self.alive:
            for kafka_event in self.consumer:
                event = DictUtils.getDefaultEventDict(dict={"topic": kafka_event.topic, "data": kafka_event.value}, caller_class_name=self.__class__.__name__)
                self.sendEvent(event)
                if(self.enable_auto_commit):
                    self.consumer.task_done(kafka_event)
                self.message_counter += 1
                if self.messages_to_read > 0 and self.message_counter >= self.messages_to_read:
                    self.alive = False
                    self.lumbermill.shutDown()
                    continue