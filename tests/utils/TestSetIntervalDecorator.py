import time
import unittest
from lumbermill.utils.Decorators import setInterval


class TestSetIntervalDecorator(unittest.TestCase):

    def setUp(self):
        self.values = []

    def collectValues(self, value):
        self.values.append(value)

    def testSetIntervalDefault(self):
        @setInterval(.3)
        def timedFunction():
            self.collectValues('spam')
        handler = timedFunction()
        time.sleep(1.1)
        handler.set()
        self.assertEquals(self.values, ['spam', 'spam', 'spam'])

    def testSetIntervalMaxRunCount(self):
        @setInterval(.1, max_run_count=3)
        def timedFunction():
            self.collectValues('spam')
        handler = timedFunction()
        time.sleep(1)
        handler.set()
        self.assertEquals(self.values, ['spam', 'spam', 'spam'])

    def testSetIntervalCallOnInit(self):
        @setInterval(.3, call_on_init=True)
        def timedFunction():
            self.collectValues('spam')
        handler = timedFunction()
        time.sleep(1.1)
        handler.set()
        self.assertEquals(self.values, ['spam', 'spam', 'spam', 'spam'])