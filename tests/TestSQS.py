import random
import time
import ModuleBaseTestCase
import os
import sys
import unittest
import mock
import boto3

import lumbermill.Utils as Utils
from lumbermill.input import SQS

class TestSQS(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        try:
            self.aws_access_key_id = os.environ['AWS_ID']
            self.aws_secret_access_key = os.environ['AWS_KEY']
        except KeyError:
            raise unittest.SkipTest('Skipping test bescause no aws credentials set. Please set env vars AWS_ID and AWS_KEY.')
        self.queue_name = "%032x%s" % (random.getrandbits(128), os.getpid())
        self.connectToSqsQueue()
        super(TestSQS, self).setUp(SQS.SQS(mock.Mock()))

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

    def testSQS(self):
        self.test_object.configure({'aws_access_key_id': os.environ['AWS_ID'],
                                    'aws_secret_access_key': os.environ['AWS_KEY'],
                                    'region': 'eu-west-1',
                                    'queue': self.queue_name})
        self.checkConfiguration()
        # Send some messages to the test queue.
        for _ in range(0, 100):
            self.sqs_queue.send_message(MessageBody='One thing is for sure, the sheep is not a creature of the air. '
                                                    'They have enormous difficulty in the comparatively simple act of perchin.')
        # Give messages some time to arrive.
        time.sleep(2)
        self.test_object.start()
        event = False
        time.sleep(2)
        counter = 0
        for event in self.receiver.getEvent():
            counter += 1
        self.assertTrue(event != False)
        self.assertEqual(counter, 100)
        self.assertEqual(event['data'], 'One thing is for sure, the sheep is not a creature of the air. '
                                        'They have enormous difficulty in the comparatively simple act of perchin.')

    def tearDown(self):
        self.sqs_client.delete_queue(QueueUrl=self.sqs_queue.url)