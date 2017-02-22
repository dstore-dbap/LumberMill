import unittest
from lumbermill.utils.Decorators import memoize


class TestSetIntervalDecorator(unittest.TestCase):

    key_lookups = 0
    data = {'val1': 1, 'val2': 2, 'val3': 3, 'val4': 4}

    def lookupKey(self, key):
        self.key_lookups += 1
        try:
            return self.data[key]
        except KeyError:
            pass

    def testMomoizeDefault(self):
        @memoize()
        def memoizedFunc(key):
            return self.lookupKey(key)
        for _ in xrange(0, 100):
            memoizedFunc('val1')
        self.assertEquals(self.key_lookups, 1)
        for _ in xrange(0, 100):
            memoizedFunc('val2')
        self.assertEquals(self.key_lookups, 2)

    def testMemoizeMaxlen(self):
        @memoize(maxlen=2)
        def memoizedFunc(key):
            return self.lookupKey(key)
        memoizedFunc('val1')
        self.assertEquals(self.key_lookups, 1)
        memoizedFunc('val2')
        self.assertEquals(self.key_lookups, 2)
        memoizedFunc('val3')
        self.assertEquals(self.key_lookups, 3)
        memoizedFunc('val1')
        self.assertEquals(self.key_lookups, 4)
