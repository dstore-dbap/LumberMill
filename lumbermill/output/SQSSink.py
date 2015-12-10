# -*- coding: utf-8 -*-
import logging
import os
import random
import boto3
import sys

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser

# For pypy the default json module is the fastest.
if Utils.is_pypy:
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
class SQSSink(BaseThreadedModule):
    """
    Send messages to amazon sqs service.

    aws_access_key_id: Your AWS id.
    aws_secret_access_key: Your AWS password.
    region: The region in which to find your sqs service.
    queue: Queue name.
    format: Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'.
            If not set event.data will be send es MessageBody, all other fields will be send as MessageAttributes.
    store_interval_in_secs: Send data to redis in x seconds intervals.
    batch_size: Number of messages to collect before starting to send messages to sqs. This refers to the internal
                receive buffer of this plugin. When the receive buffer is maxed out, this plugin will always send
                the maximum of 10 messages in one send_message_batch call.
    backlog_size: Maximum count of events waiting for transmission. Events above count will be dropped.

    values: ['us-east-1', 'us-west-1', 'us-west-2', 'eu-central-1', 'eu-west-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'sa-east-1', 'us-gov-west-1', 'cn-north-1']

    Configuration template:

    - SQSSink:
       aws_access_key_id:               # <type: string; is: required>
       aws_secret_access_key:           # <type: string; is: required>
       region:                          # <type: string; is: required>
       queue:                           # <type: string; is: required>
       format:                          # <default: None; type: None||string; is: optional>
       store_interval_in_secs:          # <default: 5; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 500; type: integer; is: optional>
       receivers:
        - NextModule
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        # Set boto log level.
        logging.getLogger('boto3').setLevel(logging.CRITICAL)
        logging.getLogger('botocore').setLevel(logging.CRITICAL)
        self.batch_size = self.getConfigurationValue('batch_size')
        self.format = self.getConfigurationValue('format')

    def getStartMessage(self):
        return "Queue: %s [%s]. Max buffer size: %d" % (self.getConfigurationValue('queue'),
                                                        self.getConfigurationValue('region'),
                                                        self.getConfigurationValue('backlog_size'))


    def initAfterFork(self):
        BaseThreadedModule.initAfterFork(self)
        self.buffer = Utils.Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))
        try:
            self.sqs_resource = boto3.resource('sqs',
                                                region_name=self.getConfigurationValue('region'),
                                                api_version=None,
                                                use_ssl=True,
                                                verify=None,
                                                endpoint_url=None,
                                                aws_access_key_id=self.getConfigurationValue('aws_access_key_id'),
                                                aws_secret_access_key=self.getConfigurationValue('aws_secret_access_key'),
                                                aws_session_token=None,
                                                config=None)
            self.sqs_queue = self.sqs_resource.get_queue_by_name(QueueName=self.getConfigurationValue('queue'))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not connect to sqs service. Exception: %s, Error: %s." % (etype, evalue))
            self.lumbermill.shutDown()

    def handleEvent(self, event):
        self.buffer.append(event)
        yield None

    def storeData(self, buffered_data):
        batch_messages = []
        for event in buffered_data:
            try:
                id = event['lumbermill']['event_id']
            except KeyError:
                id = "%032x%s" % (random.getrandbits(128), os.getpid())
            message = {'Id': id}
            if self.format:
                event = Utils.mapDynamicValue(self.format, event)
            else:
                try:
                    event = json.dumps(event)
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.warning("Error while encoding event data: %s to json. Exception: %s, Error: %s." % (event, etype, evalue))
            message['MessageBody'] = event
            batch_messages.append(message)
            if len(batch_messages) % 10:
                self.sqs_queue.send_messages(Entries=batch_messages)
                batch_messages = []
        if len(batch_messages) > 0:
            self.send()

    def shutDown(self):
        self.buffer.flush()

