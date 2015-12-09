import sys
import time
import extendSysPath
import mock
import redis
import ModuleBaseTestCase
import RedisChannel
import unittest


class TestRedisChannel(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestRedisChannel, self).setUp(RedisChannel.RedisChannel(gp=mock.Mock()))
        self.redis_host = 'localhost'
        self.redis_port = 6379
        try:
            self.client = redis.Redis(host=self.redis_host, port=self.redis_port)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error('Could no connect to redis server at %s:%s. Exception: %s, Error: %s.' % (self.redis_host, self.redis_port, etype, evalue))
            sys.exit(255)

    """
    - RedisChannel:
        channel:                    # <type: string; is: required>
        server:                     # <default: 'localhost'; type: string; is: optional>
        port:                       # <default: 6379; type: integer; is: optional>
        db:                         # <default: 0; type: integer; is: optional>
        password:                   # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule
    """
    @unittest.skip('Currently broken.')
    def test(self):
        self.test_object.configure({'channel': 'TestChannel',
                                    'server': 'localhost'})
        self.checkConfiguration()
        self.startTornadoEventLoop()
        data = "It's my belief that these sheep are laborin' under the misapprehension that they're birds."
        for _ in range(0, 500):
            self.client.publish('TestChannel', data)
        event = False
        time.sleep(1)
        counter = 0
        for event in self.receiver.getEvent():
            counter += 1
        self.assertTrue(event != False)
        self.assertEqual(counter, 500)
        self.assertEqual(event['data'], data)