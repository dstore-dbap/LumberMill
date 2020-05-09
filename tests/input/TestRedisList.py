import sys
import time
import mock
import redis

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.input import RedisList


class TestRedisList(ModuleBaseTestCase):

    def setUp(self):
        super(TestRedisList, self).setUp(RedisList.RedisList(mock.Mock()))
        redis_service = self.getRedisService()
        self.redis_host = redis_service['server']
        self.redis_port = redis_service['port']
        try:
            self.client = redis.Redis(host=self.redis_host, port=self.redis_port)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error('Could no connect to redis server at %s:%s. Exception: %s, Error: %s.' % (self.redis_host, self.redis_port, etype, evalue))
            sys.exit(255)

    """
    - RedisList:
        lists:                    # <type: list; is: required>
        server:                   # <default: 'localhost'; type: string; is: optional>
        port:                     # <default: 6379; type: integer; is: optional>
        db:                       # <default: 0; type: integer; is: optional>
        password:                 # <default: None; type: None||string; is: optional>
        timeout:                  # <default: 0; type: integer; is: optional>
        receivers:
          - NextModule
    """
    def test(self):
        self.test_object.configure({'lists': ['TestList'],
                                    'server': self.redis_host,
                                    'port': self.redis_port})
        self.checkConfiguration()
        self.test_object.start()
        data = "It's my belief that these sheep are laborin' under the misapprehension that they're birds."
        for _ in range(0, 500):
            self.client.rpush('TestList', data)
        event = False
        time.sleep(1)
        counter = 0
        for event in self.receiver.getEvent():
            counter += 1
        self.assertTrue(event != False)
        self.assertEqual(counter, 500)
        self.assertEqual(data, event['data'])