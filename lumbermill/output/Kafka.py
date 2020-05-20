# -*- coding: utf-8 -*-
import sys
import kafka

from lumbermill.constants import IS_PYPY
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser
from lumbermill.utils.DynamicValues import mapDynamicValue

# For pypy the default json module is the fastest.
if IS_PYPY:
    import json
else:
    json = False
    for module_name in ['ujson', 'yajl', 'simplejson', 'json']:
        try:
            json = __import__(module_name)
            break
        except ImportError:
            pass
    if not json:
        raise ImportError


@ModuleDocstringParser
class Kafka(BaseThreadedModule):
    """
    Publish incoming events to kafka topic.

    topic: Name of kafka topic to send data to.
    brokers: Kafka brokers to connect to.
    key: Key for compacted topics.
    format: Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'. If not set, the whole event dict is send.

    Configuration template:

    - output.Kafka:
       topic:                           # <type: string; is: required>
       brokers:                         # <default: ['localhost:9092']; type: list; is: optional>
       key:                             # <default: None; type: None||string; is: optional>
       format:                          # <default: None; type: None||string; is: optional>
    """

    module_type = "output"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.format = self.getConfigurationValue('format')
        self.has_key = True if self.getConfigurationValue('key') else False
        try:
            self.producer = kafka.KafkaProducer(bootstrap_servers=self.getConfigurationValue('brokers'))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not connect to kafka brokers at %s. Exception: %s, Error: %s." % (self.getConfigurationValue('brokers'), etype, evalue))

    def initAfterFork(self):
        #self.buffer = Utils.Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))
        BaseThreadedModule.initAfterFork(self)

    def getStartMessage(self):
        start_msg = "publishing to %s -> %s" % (self.getConfigurationValue('brokers'), self.getConfigurationValue('topic'))
        return start_msg

    def handleEvent(self, event):
        if self.format:
            publish_data = mapDynamicValue(self.format, event).encode('utf-8')
        else:
            publish_data = json.dumps(event).encode('utf-8')
        key = None
        if self.has_key:
            key = self.getConfigurationValue('key', event).encode('utf-8')
        try:
            self.producer.send(self.getConfigurationValue('topic', event), value=publish_data)
        except kafka.errors.CorruptRecordException:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not publish event to kafka topic %s at %s. Exception: %s, Error: %s." % (self.getConfigurationValue('topic', event), self.getConfigurationValue('brokers'), etype, evalue))
            self.logger.error("Maybe you are trying to publish to a compacted topic without a key set?")
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not publish event to kafka topic %s at %s. Exception: %s, Error: %s." % (self.getConfigurationValue('topic', event), self.getConfigurationValue('brokers'), etype, evalue))
        yield None

    def __handleEvent(self, event):
        if self.format:
            publish_data = mapDynamicValue(self.format, event)
        else:
            publish_data = event
        self.buffer.append(publish_data)
        yield None
