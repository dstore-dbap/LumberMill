# -*- coding: utf-8 -*-
import collections
import os
import sys
import time
from cStringIO import StringIO

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Buffers import Buffer
from lumbermill.utils.Decorators import ModuleDocstringParser, setInterval
from lumbermill.utils.DynamicValues import mapDynamicValue
from lumbermill.utils.misc import TimedFunctionManager


@ModuleDocstringParser
class FileSink(BaseThreadedModule):
    """
    Store all received events in a file.

    file_name: absolute path to filen. String my contain pythons strtime directives and event fields, e.g. %Y-%m-%d.
    format: Which event fields to use in the logline, e.g. '$(@timestamp) - $(url) - $(country_code)'
    store_interval_in_secs: sending data to es in x seconds intervals.
    batch_size: sending data to es if event count is above, even if store_interval_in_secs is not reached.
    backlog_size: maximum count of events waiting for transmission. Events above count will be dropped.
    compress: Compress output as gzip or snappy file. For this to be effective, the chunk size should not be too small.

    Configuration template:

    - FileSink:
       file_name:                       # <type: string; is: required>
       format:                          # <default: '$(data)'; type: string; is: optional>
       store_interval_in_secs:          # <default: 10; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 500; type: integer; is: optional>
       compress:                        # <default: None; type: None||string; values: [None,'gzip','snappy']; is: optional>
    """

    module_type = "output"
    """Set module type"""
    can_run_forked = False

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.batch_size = self.getConfigurationValue('batch_size')
        self.backlog_size = self.getConfigurationValue('backlog_size')
        self.file_name = self.getConfigurationValue('file_name')
        self.format = self.getConfigurationValue('format')
        self.compress = self.getConfigurationValue('compress')
        self.file_handles = {}
        if self.compress == 'gzip':
            try:
                # Import module into namespace of object. Otherwise it will not be accessible when process was forked.
                self.gzip_module = __import__('gzip')
            except ImportError:
                self.logger.error('Gzip compression selected but gzip module could not be loaded.')
                self.lumbermill.shutDown()
        if self.compress == 'snappy':
            try:
                self.snappy_module = __import__('snappy')
            except ImportError:
                self.logger.error('Snappy compression selected but snappy module could not be loaded.')
                self.lumbermill.shutDown()
        self.buffer = Buffer(self.batch_size, self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.backlog_size)
        TimedFunctionManager.startTimedFunction(self.closeStaleFileHandles)

    def getStartMessage(self):
        return "File: %s. Max buffer size: %d" % (self.file_name, self.getConfigurationValue('backlog_size'))

    def initAfterFork(self):
        BaseThreadedModule.initAfterFork(self)
        # As the buffer uses a threaded timed function to flush its buffer and thread will not survive a fork, init buffer here.
        self.buffer = Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))
        BaseThreadedModule.initAfterFork(self)

    @setInterval(60)
    def closeStaleFileHandles(self):
        """
        Close and delete file handles that are unused since 5 minutes.
        """
        for path, file_handle_data in self.file_handles.items():
            last_used_time_ago = time.time() - file_handle_data['lru']
            if last_used_time_ago < 300:
                continue
            self.logger.info('Closing stale file handle for %s.' % (path))
            file_handle_data['handle'].close()
            self.file_handles.pop(path)

    def closeAllFileHandles(self):
        for path, file_handle_data in self.file_handles.items():
            self.logger.info('Closing file handle for %s.' % path)
            file_handle_data['handle'].close()
            self.file_handles.pop(path)

    def ensurePathExists(self, path):
        dirpath = os.path.dirname(path)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

    def handleEvent(self, event):
        self.buffer.append(event)
        yield None

    def getOrCreateFileHandle(self, path, mode):
        file_handle = None
        try:
            file_handle = self.file_handles[path]['handle']
            self.file_handles[path]['lru'] = time.time()
        except KeyError:
            try:
                file_handle = open(path, mode)
                self.file_handles[path] = {'handle': file_handle, 'lru': time.time()}
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error('Could no open %s for writing. Exception: %s, Error: %s.' % (path, etype, evalue))
        return file_handle

    def storeData(self, events):
        write_data = collections.defaultdict(str)
        for event in events:
            path = mapDynamicValue(self.file_name, mapping_dict=event, use_strftime=True)
            line = mapDynamicValue(self.format, mapping_dict=event)
            write_data["%s" % path] += line + "\n"
        for path, lines in write_data.items():
            try:
                self.ensurePathExists(path)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error('Could no create path %s. Events could not be written. Exception: %s, Error: %s.' % (path, etype, evalue))
                return
            mode = "a+"
            if self.compress == 'gzip':
                path += ".gz"
                mode += "b"
                lines = self.compressGzip(lines)
            elif self.compress == 'snappy':
                path += ".snappy"
                lines = self.compressSnappy(lines)
                mode += "b"
            try:
                fh = self.getOrCreateFileHandle(path, mode)
                fh.write(lines)
                return True
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error('Could no write event data to %s. Exception: %s, Error: %s.' % (path, etype, evalue))

    def shutDown(self):
        self.buffer.flush()
        self.closeAllFileHandles()
        BaseThreadedModule.shutDown(self)

    def compressGzip(self, data):
        buffer = StringIO()
        compressor = self.gzip_module.GzipFile(mode='wb', fileobj=buffer)
        try:
            compressor.write(data)
        finally:
            compressor.close()
        return buffer.getvalue()

    def compressSnappy(self, data):
        return self.snappy_module.compress(data)
