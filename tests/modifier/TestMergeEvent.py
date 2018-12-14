import os
import time
import mock
import pprint
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.modifier import MergeEvent


class TestMergeEvent(ModuleBaseTestCase):

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
            event = DictUtils.getDefaultEventDict({'data': input_line}, received_from='TestMergeEvent_%s' % os.getpid())
            self.test_object.receiveEvent(event)
        time.sleep(1)
        events = []
        for event in self.receiver.getEvent():
            events.append(event)
        pprint.pprint(events)
        self.assertEquals(len(events), 3)

    def testMergeEventWithNonMatchingLines(self):
        example_input_data = """Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever.
        Spam, Spam, Spam, lovely Spam
        Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever.
        Wonderful Spam, Lovely Spam."""
        self.test_object.configure({'pattern': '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+ [^]]*\]'})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        for input_line in example_input_data.split("\n"):
            event = DictUtils.getDefaultEventDict({'data': input_line}, received_from='TestMergeEvent_%s' % os.getpid())
            self.test_object.receiveEvent(event)
        time.sleep(1)
        events = []
        for event in self.receiver.getEvent():
            events.append(event)
        self.assertEquals(len(events), 4)

    def testMergeEventWithMixedMatchingLines(self):
        example_input_data = """2015-02-18 14:25:10,661 [http-bio-8080] ERROR errors.GrailsExceptionResolver  - IllegalArgumentException occurred when processing request: [GET] /en
no category found for name: en. Stacktrace follows:
java.lang.IllegalArgumentException: no category found for name: en
	at de.dbap.data.ECategory.getByName(ECategory.java:26)
	at de.dbap.controller.FacetedNavController.index(FacetedNavController.groovy:37)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
	at java.lang.Thread.run(Thread.java:745)
2015-02-18 14:52:00,829 [http-bio-8080] Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever.
2015-02-18 14:52:08,829 [http-bio-8080] ERROR errors.GrailsExceptionResolver  - IllegalArgumentException occurred when processing request: [GET] /en
no category found for name: en. Stacktrace follows:
java.lang.IllegalArgumentException: no category found for name: en
	at de.dbap.data.ECategory.getByName(ECategory.java:26)
	at de.dbap.controller.FacetedNavController.index(FacetedNavController.groovy:37)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
	at java.lang.Thread.run(Thread.java:745)
2015-02-18 14:53:01,829 [http-bio-8080] Beethoven, Mozart, Chopin, Liszt, Brahms, Panties...I'm sorry...Schumann, Schubert, Mendelssohn and Bach. Names that will live for ever.
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
            event = DictUtils.getDefaultEventDict({'data': input_line}, received_from='TestMergeEvent_%s' % os.getpid())
            self.test_object.receiveEvent(event)
        time.sleep(1.5)
        events = []
        for event in self.receiver.getEvent():
            events.append(event)
        self.assertEquals(len(events), 5)

    def testNewlineEndEvent(self):
        self.test_object.configure({'pattern': "\n$",
                                    'pattern_marks': 'EndOfEvent'})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        event = DictUtils.getDefaultEventDict({'data': 'No newline.'}, received_from='TestMergeEvent_%s' % os.getpid())
        self.test_object.receiveEvent(event)
        event = DictUtils.getDefaultEventDict({'data': "But now: \n"}, received_from='TestMergeEvent_%s' % os.getpid())
        self.test_object.receiveEvent(event)
        time.sleep(1.5)
        events = []
        for event in self.receiver.getEvent():
            events.append(event)
        self.assertEquals(len(events), 1)
        self.assertEquals(events[0]['data'], 'No newline.But now: \n')