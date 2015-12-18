import random
import time
import ModuleBaseTestCase
import os
import sys
import unittest
import mock
import json
import boto3

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.output import SQSSink

class TestSQSSink(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        try:
            self.aws_access_key_id = os.environ['AWS_ID']
            self.aws_secret_access_key = os.environ['AWS_KEY']
        except KeyError:
            raise unittest.SkipTest('Skipping test bescause no aws credentials set. Please set env vars AWS_ID and AWS_KEY.')
        self.queue_name = "%032x%s" % (random.getrandbits(128), os.getpid())
        self.connectToSqsQueue()
        super(TestSQSSink, self).setUp(SQSSink.SQSSink(mock.Mock()))

    def connectToSqsQueue(self):
        try:
            self.sqs_client = boto3.client('sqs', region_name='eu-west-1',
                                                  api_version=None,
                                                  use_ssl=True,
                                                  verify=None,
                                                  endpoint_url=None,
                                                  aws_access_key_id=self.aws_access_key_id,
                                                  aws_secret_access_key=self.aws_secret_access_key,
                                                  aws_session_token=None,
                                                  config=None)
            self.sqs_resource = boto3.resource('sqs', region_name='eu-west-1',
                                                      api_version=None,
                                                      use_ssl=True,
                                                      verify=None,
                                                      endpoint_url=None,
                                                      aws_access_key_id=self.aws_access_key_id,
                                                      aws_secret_access_key=self.aws_secret_access_key,
                                                      aws_session_token=None,
                                                      config=None)
            self.sqs_queue = self.sqs_resource.create_queue(QueueName=self.queue_name)
        except:
            etype, evalue, etb = sys.exc_info()
            print "Could not create sqs queue %s. Exception: %s, Error: %s" % (self.queue_name, etype, evalue)

    def testSQSSink(self):
        self.test_object.configure({'aws_access_key_id': os.environ['AWS_ID'],
                                    'aws_secret_access_key': os.environ['AWS_KEY'],
                                    'region': 'eu-west-1',
                                    'queue': self.queue_name})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        # Send some messages to the test queue.
        for _ in range(0, 100):
            event = DictUtils.getDefaultEventDict({u'data': u"You get 'Gone with the Wind', 'Les Miserables' by Victor Hugo, "
                                                        u"'The French Lieutenant's Woman' and with every third book you get dung."})
            self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        # Give messages some time to arrive.
        time.sleep(2)
        # Get messages from queue
        messages = []
        for _ in range(0, 50):
            response = self.sqs_client.receive_message(QueueUrl=self.sqs_queue.url,
                                                       MaxNumberOfMessages=10)
            if not 'Messages' in response:
                break
            for message in response['Messages']:
                messages.append(message)
        self.assertEqual(len(messages), 100)
        self.assertEqual(json.loads(messages[0]['Body'])['data'], event['data'])

    def tearDown(self):
        self.sqs_client.delete_queue(QueueUrl=self.sqs_queue.url)