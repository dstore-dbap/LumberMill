import os
import time
import ModuleBaseTestCase
import mock

import lumbermill.Utils as Utils
from lumbermill.modifier import MergeEvent


class TestMergeEvent(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestMergeEvent, self).setUp(MergeEvent.MergeEvent(mock.Mock()))

    def testMergeEventWithMatchingLines(self):
        example_input_data = """2015-02-18 14:25:10,661 [http-bio-8080] ERROR errors.GrailsExceptionResolver  - IllegalArgumentException occurred when processing request: [GET] /en
no category found for name: en. Stacktrace follows:
java.lang.IllegalArgumentException: no category found for name: en
	at de.dbap.data.ECategory.getByName(ECategory.java:26)
	at de.dbap.controller.FacetedNavController.index(FacetedNavController.groovy:37)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
	at java.lang.Thread.run(Thread.java:745)
2015-02-18 14:52:08,829 [http-bio-8080] ERROR errors.GrailsExceptionResolver  - IllegalArgumentException occurred when processing request: [GET] /en
no category found for name: en. Stacktrace follows:
java.lang.IllegalArgumentException: no category found for name: en
	at de.dbap.data.ECategory.getByName(ECategory.java:26)
	at de.dbap.controller.FacetedNavController.index(FacetedNavController.groovy:37)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
	at java.lang.Thread.run(Thread.java:745)
2015-02-18 14:53:35,493 [http-bio-8080] ERROR errors.GrailsExceptionResolver  - IllegalArgumentException occurred when processing request: [GET] /en
no category found for name: en. Stacktrace follows:
java.lang.IllegalArgumentException: no category found for name: en
	at de.dbap.data.ECategory.getByName(ECategory.java:26)
	at de.dbap.controller.FacetedNavController.index(FacetedNavController.groovy:37)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
	at java.lang.Thread.run(Thread.java:745)"""
        self.test_object.configure({'pattern': '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+ [^]]*\]'})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        for input_line in example_input_data.split("\n"):
            event = Utils.getDefaultEventDict({'data': input_line}, received_from='TestMergeEvent_%s' % os.getpid())
            self.test_object.receiveEvent(event)
        time.sleep(1)
        event = False
        counter = 0
        for event in self.receiver.getEvent():
            counter += 1
        self.assertTrue(event != False)
        self.assertEqual(counter, 3)

    def testMergeEventWithNonMatchingLines(self):
        example_input_data = """Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever.
        Spam, Spam, Spam, lovely Spam
        Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever.
        Wonderful Spam, Lovely Spam."""
        self.test_object.configure({'pattern': '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+ [^]]*\]'})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        for input_line in example_input_data.split("\n"):
            event = Utils.getDefaultEventDict({'data': input_line}, received_from='TestMergeEvent_%s' % os.getpid())
            self.test_object.receiveEvent(event)
        time.sleep(1)
        event = False
        counter = 0
        for event in self.receiver.getEvent():
            counter += 1
        self.assertTrue(event != False)
        self.assertEqual(counter, 4)