import copy
import time
import sys
import tempfile

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.constants import LUMBERMILL_BASEPATH
from lumbermill.input import File


class TestFile(ModuleBaseTestCase):

    def setUp(self):
        test_object = File.File(MockLumberMill())
        super(TestFile, self).setUp(test_object)
        self.temp_file = None

    def testAbsoluteFilePath(self):
        self.test_object.configure({'paths': LUMBERMILL_BASEPATH + '/../tests/test_data/file_input/cheese.py'})
        self.test_object.checkConfiguration()
        self.assertEquals(self.test_object.files, [LUMBERMILL_BASEPATH + '/../tests/test_data/file_input/cheese.py'])

    def testMultipleFilePaths(self):
        self.test_object.configure({'paths': [LUMBERMILL_BASEPATH + '/../tests/test_data/file_input/',
                                              LUMBERMILL_BASEPATH + '/../tests/test_data/file_input/second_level']})
        self.test_object.checkConfiguration()
        self.assertEquals(len(self.test_object.files), 6)

    def testFindFilesNotRecursive(self):
        self.test_object.configure({'paths': LUMBERMILL_BASEPATH + '/../tests/test_data/file_input/'})
        self.test_object.checkConfiguration()
        self.assertEquals(len(self.test_object.files), 4)

    def testFindFilesRecursive(self):
        self.test_object.configure({'paths': LUMBERMILL_BASEPATH + '/../tests/test_data/file_input',
                                    'recursive': True})
        self.test_object.checkConfiguration()
        self.assertEquals(len(self.test_object.files), 7)

    def testFindFilesWithPattern(self):
        self.test_object.configure({'paths': LUMBERMILL_BASEPATH + '/../tests/test_data/file_input',
                                    'recursive': True,
                                    'pattern': '*.info'})
        self.test_object.checkConfiguration()
        self.assertEquals(len(self.test_object.files), 2)
        self.assertEquals(self.test_object.files[1], LUMBERMILL_BASEPATH + '/../tests/test_data/file_input/second_level_2/spam.info')

    def testReadFileComplete(self):
        self.test_object.configure({'paths': LUMBERMILL_BASEPATH + '/../tests/test_data/file_input',
                                    'recursive': True,
                                    'pattern': 'spam.info'})
        self.test_object.checkConfiguration()
        self.test_object.start()
        time.sleep(.2)
        for event in self.receiver.getEvent():
            self.assertEquals(event['data'], 'Spam!\nSpam! Spam!\nSpam! Spam! Spam!')

    def testReadFileLineByLine(self):
        self.test_object.configure({'paths': LUMBERMILL_BASEPATH + '/../tests/test_data/file_input',
                                    'recursive': True,
                                    'pattern': 'spam.info',
                                    'line_by_line': True})
        self.test_object.checkConfiguration()
        self.test_object.start()
        time.sleep(.2)
        line_counter = 0
        for event in self.receiver.getEvent():
            line_counter += 1
        self.assertEquals(line_counter, 3)
        self.assertEquals(event['data'], 'Spam! Spam! Spam!')

    def testFileTailMode(self):
        self.temp_file = tempfile.NamedTemporaryFile()
        self.test_object.configure({'log_level': 'info',
                                    'paths': self.temp_file.name,
                                    'line_by_line': True,
                                    'mode': 'tail',
                                    'stat_interval': .1})
        self.test_object.checkConfiguration()
        self.test_object.start()
        # Give tail threads a bit time to initialize.
        time.sleep(.2)
        self.temp_file.write("Spam!\nSpam! Spam!\nSpam! Spam! Spam!\n")
        # Force os to flush data to file.
        self.temp_file.read()
        time.sleep(.2)
        events = []
        for event in self.receiver.getEvent():
            events.append(event)
        self.assertTrue(len(events) == 3)
        self.assertTrue(events[0]['data'] == "Spam!")
        self.assertTrue(events[1]['data'] == "Spam! Spam!")
        self.assertTrue(events[2]['data'] == "Spam! Spam! Spam!")

    def testDivideFilesToMultipleWorkers(self):
        worker_count = 3
        # Total found files should be 7.
        self.test_object.configure({'paths': LUMBERMILL_BASEPATH + '/../tests/test_data/file_input',
                                    'recursive': True,
                                    'line_by_line': True})
        self.test_object.checkConfiguration()
        self.test_object.lumbermill.setWorkerCount(worker_count)
        all_files = copy.copy(self.test_object.files)
        worker_files = []
        for _ in xrange(0, self.test_object.lumbermill.getWorkerCount()):
            self.test_object.initAfterFork()
            worker_files.append(copy.copy(self.test_object.files))
            self.test_object.files = copy.copy(all_files)
            self.test_object.lumbermill.is_master_process = False
        # First worker should take care of 3 files, since it is the master.
        self.assertEquals(len(worker_files[0]), 3)
        # Second and third should each take care of 2 files.
        self.assertEquals(len(worker_files[1]), 2)
        self.assertEquals(len(worker_files[2]), 2)
        self.assertNotEquals(worker_files[0], worker_files[1])
        self.assertNotEquals(worker_files[0], worker_files[2])
        self.assertNotEquals(worker_files[1], worker_files[2])
        for worker_number, files in enumerate(worker_files):
            for file in files:
                try:
                    all_files.remove(file)
                except ValueError:
                    pass
        self.assertEquals(all_files, [])

    def tearDown(self):
        ModuleBaseTestCase.tearDown(self)
        if self.temp_file:
            try:
                self.temp_file.close()
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Could not remove temporary file %s" % self.temp_file.name)