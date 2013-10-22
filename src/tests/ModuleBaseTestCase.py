import extendSysPath
import unittest
import Queue
import Utils

class ModuleBaseTestCase(unittest.TestCase):

    def setUp(self, test_object):
        self.input_queue = Queue.Queue()
        self.output_queue = Queue.Queue()
        self.test_object = test_object
        self.test_object.setup()
        self.test_object.setInputQueue(self.input_queue)
        self.test_object.addOutputQueue(self.output_queue, filter_by_marker=False, filter_by_field=False)

    def testQueueCommunication(self, config = {}):
        self.test_object.configure(config)
        self.test_object.start()
        self.input_queue.put(Utils.getDefaultDataDict({}))
        queue_emtpy = False
        try:
            self.output_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy != True)

    def testWorksOnOriginal(self, config = {}):
        config['work-on-copy'] = False
        data_dict = Utils.getDefaultDataDict({})
        self.test_object.configure(config)
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        try:
            returned_data_dict = self.output_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy != True and returned_data_dict is data_dict)

    def testWorksOnCopy(self, config = {}):
        config['work-on-copy'] = True
        data_dict = Utils.getDefaultDataDict({})
        self.test_object.configure(config)
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        try:
            returned_data_dict = self.output_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy != True and returned_data_dict is not data_dict)

    def testOutputQueueFilter(self, config = {}):
        filtered_queue = Queue.Queue()
        data_dict = Utils.getDefaultDataDict({})
        self.test_object.configure(config)
        self.test_object.addOutputQueue(filtered_queue, filter_by_marker=False, filter_by_field="not_existing_field_name")
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        try:
            filtered_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy == True)

    def testInvertedOutputQueueFilter(self,config = {}):
        filtered_queue = Queue.Queue()
        data_dict = Utils.getDefaultDataDict({})
        self.test_object.configure(config)
        self.test_object.addOutputQueue(filtered_queue, filter_by_marker=False, filter_by_field="!not_existing_field_name")
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        returned_data_dict = {}
        try:
            returned_data_dict = filtered_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy != True and 'data' in returned_data_dict)