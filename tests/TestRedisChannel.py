import sys
import time
import mock
import redis
import ModuleBaseTestCase

from lumbermill.input import RedisChannel


class TestRedisChannel(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestRedisChannel, self).setUp(RedisChannel.RedisChannel(mock.Mock()))
        self.redis_host = 'localhost'
        self.redis_port = 6379
        try:
            self.client = redis.Redis(host=self.redis_host, port=self.redis_port)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error('Could no connect to redis server at %s:%s. Exception: %s, Error: %s.' % (self.redis_host, self.redis_port, etype, evalue))
            sys.exit(255)

    def testDefaultvalues(self):
        self.test_object.configure({'channel': 'TestChannel'})
        self.checkConfiguration()
        self.startTornadoEventLoop()
        data = "It's my belief that these sheep are laborin' under the misapprehension that they're birds."
        for _ in range(0, 100):
            self.client.publish('TestChannel', data)
        event = None
        time.sleep(1)
        counter = 0
        for event in self.receiver.getEvent():
            counter += 1
        self.assertIsNotNone(event)
        self.assertEqual(counter, 100)
        self.assertEqual(event['data'], data)