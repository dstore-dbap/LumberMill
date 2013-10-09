from docutils.nodes import danger
import extendSysPath
import unittest
import re
import Queue
import Utils
import AddDateTime

class TestAddDateTime(unittest.TestCase):
    def setUp(self):
        self.input_queue = Queue.Queue()
        self.output_queue = Queue.Queue()
        self.test_object = AddDateTime.AddDateTime()
        self.test_object.setup()
        self.test_object.setInputQueue(self.input_queue)
        self.test_object.addOutputQueue(self.output_queue, filter_by_marker=False, filter_by_field=False)

    def testIsTimeStamp(self):
        self.test_object.configure({})
        dict_with_date = self.test_object.handleData(Utils.getDefaultDataDict({}))
        self.assert_(re.match('^\d+-\d+-\d+T\d+:\d+:\d+$', dict_with_date['@timestamp'])) # 2013-08-29T10:25:26
    
    def testAddDateTimeDefaultField(self):
        self.test_object.configure({})
        dict_with_date = self.test_object.handleData(Utils.getDefaultDataDict({}))
        self.assert_('@timestamp' in dict_with_date)

    def testAddDateTimeCustomField(self):
        self.test_object.configure({'field': 'test'})
        dict_with_date = self.test_object.handleData(Utils.getDefaultDataDict({}))
        self.assert_('test' in dict_with_date)

    def testQueueCommunication(self):
        self.test_object.start()
        self.input_queue.put(Utils.getDefaultDataDict({}))
        queue_emtpy = False
        try:
            self.output_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy != True)

    def testWorksOnOriginal(self):
        data_dict = Utils.getDefaultDataDict({})
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        try:
            dict_with_date = self.output_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy != True and dict_with_date is data_dict)

    def testWorksOnCopy(self):
        data_dict = Utils.getDefaultDataDict({})
        self.test_object.configure({'work_on_copy': True})
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        try:
            dict_with_date = self.output_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy != True and dict_with_date is not data_dict)

    def testOutputQueueFilter(self):
        filtered_queue = Queue.Queue()
        data_dict = Utils.getDefaultDataDict({})
        self.test_object.configure({'work_on_copy': False})
        self.test_object.addOutputQueue(filtered_queue, filter_by_marker=False, filter_by_field="not_existing_field_name")
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        try:
            filtered_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy == True)

    def testInvertedOutputQueueFilter(self):
        filtered_queue = Queue.Queue()
        data_dict = Utils.getDefaultDataDict({})
        self.test_object.configure({'work_on_copy': False})
        self.test_object.addOutputQueue(filtered_queue, filter_by_marker=False, filter_by_field="!not_existing_field_name")
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        try:
            dict_with_date = filtered_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy != True and '@timestamp' in dict_with_date)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()