# -*- coding: utf-8 -*-
import logging
import sys
import time
import boto3

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class SQS(BaseThreadedModule):
    """
    Read messages from amazon sqs service.

    aws_access_key_id: Your AWS id.
    aws_secret_access_key: Your AWS password.
    region: The region in which to find your sqs service.
    queue: Queue name.
    attribute_names: A list of attributes that need to be returned along with each message.
    message_attribute_names: A list of message attributes that need to be returned.
    poll_interval_in_secs: How often should the queue be checked for new messages.
    batch_size: Number of messages to retrieve in one call.

    Configuration template:

    - SQS:
       aws_access_key_id:               # <type: string; is: required>
       aws_secret_access_key:           # <type: string; is: required>
       region:                          # <type: string; is: required; values: ['us-east-1', 'us-west-1', 'us-west-2', 'eu-central-1', 'eu-west-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'sa-east-1', 'us-gov-west-1', 'cn-north-1']>
       queue:                           # <type: string; is: required>
       attribute_names:                 # <default: ['All']; type: list; is: optional>
       message_attribute_names:         # <default: ['All']; type: list; is: optional>
       poll_interval_in_secs:           # <default: 1; type: integer; is: optional>
       batch_size:                      # <default: 10; type: integer; is: optional>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        # Set boto log level.
        logging.getLogger('boto3').setLevel(logging.CRITICAL)
        logging.getLogger('botocore').setLevel(logging.CRITICAL)
        self.sqs_queue_name = self.getConfigurationValue('queue')
        self.attribute_names = self.getConfigurationValue('attribute_names')
        self.message_attribute_names = self.getConfigurationValue('message_attribute_names')
        self.poll_interval = self.getConfigurationValue('poll_interval_in_secs')
        self.batch_size = self.getConfigurationValue('batch_size')
        try:
            self.sqs_client = boto3.client('sqs', region_name=self.getConfigurationValue('region'),
                                                  api_version=None,
                                                  use_ssl=True,
                                                  verify=None,
                                                  endpoint_url=None,
                                                  aws_access_key_id=self.getConfigurationValue('aws_access_key_id'),
                                                  aws_secret_access_key=self.getConfigurationValue('aws_secret_access_key'),
                                                  aws_session_token=None,
                                                  config=None)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not connect to sqs service. Exception: %s, Error: %s." % (etype, evalue))
            self.lumbermill.shutDown()
        try:
            self.sqs_queue_url = self.sqs_client.get_queue_url(QueueName=self.sqs_queue_name)['QueueUrl']
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not get queue url for sqs queue %s. Exception: %s, Error: %s." % (self.sqs_queue_name, etype, evalue))
            self.lumbermill.shutDown()

    def run(self):
        while self.alive:
            messages_to_delete = []
            response = self.sqs_client.receive_message(QueueUrl=self.sqs_queue_url,
                                                       MaxNumberOfMessages=self.batch_size,
                                                       AttributeNames=self.attribute_names,
                                                       MessageAttributeNames=self.message_attribute_names)
            if 'Messages' not in response:
                time.sleep(self.poll_interval)
                continue
            for message in response['Messages']:
                event = Utils.getDefaultEventDict({"data": message['Body']}, caller_class_name="Sqs")
                event['sqs'] = {'attributes': message['Attributes'],
                                'id': message['MessageId'],
                                'md5_of_body': message['MD5OfBody'],
                                'md5_of_message_attributes': message.get('MD5OfMessageAttributes', None),
                                'message_attributes': message.get('MessageAttributes', None)}
                messages_to_delete.append({'Id': message['MessageId'],
                                           'ReceiptHandle': message['ReceiptHandle']})
                self.sendEvent(event)
            self.sqs_client.delete_message_batch(QueueUrl=self.sqs_queue_url, Entries=messages_to_delete)
        self.lumbermill.shutDown()