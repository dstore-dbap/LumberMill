import copy
import time
import os
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
        self.assertEqual(self.test_object.files, [LUMBERMILL_BASEPATH + '/../tests/test_data/file_input/cheese.py'])

    def testMultipleFilePaths(self):
        self.test_object.configure({'paths': [LUMBERMILL_BASEPATH + '/../tests/test_data/file_input/',
                                              LUMBERMILL_BASEPATH + '/../tests/test_data/file_input/second_level']})
        self.test_object.checkConfiguration()
        self.assertEqual(len(self.test_object.files), 6)

    def testFindFilesNotRecursive(self):
        self.test_object.configure({'paths': LUMBERMILL_BASEPATH + '/../tests/test_data/file_input/'})
        self.test_object.checkConfiguration()
        self.assertEqual(len(self.test_object.files), 4)

    def testFindFilesRecursive(self):
        self.test_object.configure({'paths': LUMBERMILL_BASEPATH + '/../tests/test_data/file_input',
                                    'recursive': True})
        self.test_object.checkConfiguration()
        self.assertEqual(len(self.test_object.files), 7)

    def testFindFilesWithPattern(self):
        self.test_object.configure({'paths': LUMBERMILL_BASEPATH + '/../tests/test_data/file_input',
                                    'recursive': True,
                                    'pattern': '*.info'})
        self.test_object.checkConfiguration()
        self.assertEqual(len(self.test_object.files), 2)
        self.assertEqual(self.test_object.files[1], LUMBERMILL_BASEPATH + '/../tests/test_data/file_input/second_level_2/spam.info')

    def testReadFileComplete(self):
        self.test_object.configure({'paths': LUMBERMILL_BASEPATH + '/../tests/test_data/file_input',
                                    'recursive': True,
                                    'pattern': 'spam.info'})
        self.test_object.checkConfiguration()
        self.test_object.start()
        time.sleep(.2)
        for event in self.receiver.getEvent():
            self.assertEqual(event['data'], 'Spam!\nSpam! Spam!\nSpam! Spam! Spam!')

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
        self.assertEqual(line_counter, 3)
        self.assertEqual(event['data'], 'Spam! Spam! Spam!')

    def testFileTailMode(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        tmp_file_path = self.temp_file.name
        self.test_object.configure({'log_level': 'info',
                                    'paths': tmp_file_path,
                                    'line_by_line': True,
                                    'mode': 'tail',
                                    'stat_interval': .1})
        self.test_object.checkConfiguration()
        self.test_object.start()
        # Give tail threads a bit time to initialize.
        time.sleep(.2)
        self.temp_file.write("Spam!\nSpam! Spam!\nSpam! Spam! Spam!\n")
        # Force os to flush data to file.
        self.temp_file.close()
        time.sleep(1)
        events = []
        for event in self.receiver.getEvent():
            events.append(event)
        self.assertTrue(len(events) == 3)
        self.assertTrue(events[0]['data'] == "Spam!")
        self.assertTrue(events[1]['data'] == "Spam! Spam!")
        self.assertTrue(events[2]['data'] == "Spam! Spam! Spam!")
        os.unlink(tmp_file_path)

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
        for _ in range(0, self.test_object.lumbermill.getWorkerCount()):
            self.test_object.initAfterFork()
            worker_files.append(copy.copy(self.test_object.files))
            self.test_object.files = copy.copy(all_files)
            self.test_object.lumbermill.is_master_process = False
        # First worker should take care of 3 files, since it is the master.
        self.assertEqual(len(worker_files[0]), 3)
        # Second and third should each take care of 2 files.
        self.assertEqual(len(worker_files[1]), 2)
        self.assertEqual(len(worker_files[2]), 2)
        self.assertNotEqual(worker_files[0], worker_files[1])
        self.assertNotEqual(worker_files[0], worker_files[2])
        self.assertNotEqual(worker_files[1], worker_files[2])
        for worker_number, files in enumerate(worker_files):
            for file in files:
                try:
                    all_files.remove(file)
                except ValueError:
                    pass
        self.assertEqual(all_files, [])

    def tearDown(self):
        ModuleBaseTestCase.tearDown(self)
        if self.temp_file:
            try:
                self.temp_file.close()
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Could not remove temporary file %s" % self.temp_file.name)