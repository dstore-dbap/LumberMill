import time

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.input import Spam


class TestSpam(ModuleBaseTestCase):

    def setUp(self):
        super(TestSpam, self).setUp(Spam.Spam(MockLumberMill()))

    def testSpamWithSingleDict(self):
        self.test_object.configure({'event': {'Lobster': 'Thermidor', 'Truffle': 'Pate'},
                                    'events_count': 985})
        self.checkConfiguration()
        self.test_object.start()
        count = 0
        time.sleep(1)
        for event in self.receiver.getEvent():
            count += 1
        self.assertEqual(event['Lobster'], 'Thermidor')
        self.assertEqual(event['Truffle'], 'Pate')
        self.assertEqual(count, 985)

    def testSpamWithSingleString(self):
        self.test_object.configure({'event': 'How to recognize different types of trees from quite a long way away.',
                                   'events_count': 42})
        self.checkConfiguration()
        self.test_object.start()
        count = 0
        time.sleep(1)
        for event in self.receiver.getEvent():
            count += 1
        self.assertEqual(event['data'], 'How to recognize different types of trees from quite a long way away.')
        self.assertEqual(count, 42)

    def testSpamWithMultipleDict(self):
        self.test_object.configure({'event': [{'Lobster': 'Thermidor', 'Truffle': 'Pate'},
                                              {'Lovely': 'Spam', 'Twit': 'of the year'}],
                                    'events_count': 42})
        self.checkConfiguration()
        self.test_object.start()
        count = 0
        time.sleep(1)
        for event in self.receiver.getEvent():
            if count % 2 == 0:
                self.assertEqual(event['Lobster'], 'Thermidor')
                self.assertEqual(event['Truffle'], 'Pate')
            else:
                self.assertEqual(event['Lovely'], 'Spam')
                self.assertEqual(event['Twit'], 'of the year')
            count += 1
        self.assertEqual(count, 42)

    def testSpamWithMultipleString(self):
        self.test_object.configure({'event': ['How to recognize different types of trees from quite a long way away.',
                                              'Number one: the larch.'],
                                    'events_count': 42})
        self.checkConfiguration()
        self.test_object.start()
        count = 0
        time.sleep(1)
        for event in self.receiver.getEvent():
            if count % 2 == 0:
                self.assertEqual(event['data'], 'How to recognize different types of trees from quite a long way away.')
            else:
                self.assertEqual(event['data'], 'Number one: the larch.')
            count += 1
        self.assertEqual(count, 42)

    def testDistributeSpamToMultipleWorkers(self):
        worker_count = 3
        self.test_object.configure({'event': ['How to recognize different types of trees from quite a long way away.',
                                              'Number one: the larch.'],
                                    'events_count': 7})
        self.test_object.checkConfiguration()
        self.test_object.lumbermill.setWorkerCount(worker_count)
        for _ in range(0, self.test_object.lumbermill.getWorkerCount()):
            self.test_object.initAfterFork()
            if self.test_object.lumbermill.is_master_process:
                self.assertEqual(self.test_object.max_events_count, 3)
                self.test_object.lumbermill.is_master_process = False
            else:
                self.assertEqual(self.test_object.max_events_count, 2)