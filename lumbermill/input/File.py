# -*- coding: utf-8 -*-
import fnmatch
import os
import random
import types

import time

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils import DictUtils
from lumbermill.utils.Decorators import ModuleDocstringParser
from lumbermill.misc.beaver.worker.tail import Tail

@ModuleDocstringParser
class File(BaseThreadedModule):
    """

    Read data from files.

    This module supports two modes:
     - cat: Just cat existing files.
     - tail: Follow changes in given files.

    paths:              An array of paths to scan for files. Can also point to a file directly.
    pattern:            Pattern the filenames need to match. E.g. '*.pdf', 'article*.xml' etc.
    recursive:          If set to true, scan paths recursively else only scan current dir.
    line_by_line:       If set to true, each line in a file will be emitted as single event.
                        If set to false, the whole file will be send as single event.
                        Only relevant for <cat> mode.
    separator:          Line separator.
    mode:               Mode <cat> will just dump out the current content of a file, <tail> will follow file changes.
    sincedb_path:       Path to a sqlite3 db file which stores the file position data since last poll.
    ignore_empty:       If True ignore empty files.
    ignore_truncate:    If True ignore truncation of files.
    sincedb_write_interval: Number of seconds to pass between update of sincedb data.
    start_position:     Where to start in the file when tailing.
    stat_interval:      Number of seconds to pass before checking for file changes.
    size_limit:         Set maximum file size for files to watch. Files exeeding this limit will be ignored. TOOD!!!

    Configuration template:

    - File:
       paths:                           # <type: string||list; is: required>
       pattern:                         # <default: '*'; type: string; is: optional>
       recursive:                       # <default: False; type: boolean; is: optional>
       line_by_line:                    # <default: False; type: boolean; is: optional>
       separator:                       # <default: "\\n"; type: string; is: optional>
       mode:                            # <default: 'cat'; type: string; is: optional; values: ['cat', 'tail']>
       sincedb_path:                    # <default: '/tmp/lumbermill_file_input_sqlite.db'; type: string; is: optional;>
       ignore_empty:                    # <default: False; type: boolean; is: optional;>
       ignore_truncate:                 # <default: False; type: boolean; is: optional;>
       sincedb_write_interval:          # <default: 15; type: integer; is: optional;>
       start_position:                  # <default: 'end'; type: string; is: optional; values: ['beginning', 'end']>
       stat_interval:                   # <default: 1; type: integer||float; is: optional;>
       tail_lines:                      # <default: False; type: boolean; is: optional;>
       size_limit:                      # <default: None; type: None||integer; is: optional;>
       multiline_regex_before:          # <default: None; type: None||integer; is: optional;>
       multiline_regex_after:           # <default: None; type: None||integer; is: optional;>
       encoding:                        # <default: 'utf_8'; type: string; is: optional;>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
        # Call parent configure method.
        BaseThreadedModule.configure(self, configuration)
        self.file_tailer = None
        self.files = self.scanPaths()
        self.line_by_line = self.getConfigurationValue('line_by_line')
        self.mode = self.getConfigurationValue('mode')
        self.datastore_key = "%032x%s" % (random.getrandbits(128), self.process_id)
        self.total_file_count = len(self.files)
        self.lumbermill.setInInternalDataStore(self.datastore_key, 0)

    def scanPaths(self):
        found_files = []
        paths = self.getConfigurationValue('paths')
        if isinstance(paths, types.StringType):
            paths = [paths]
        for path in paths:
            if os.path.isfile(path):
                found_files.append(path)
                continue
            for root, dirs, files in os.walk(path):
                for basename in files:
                    if fnmatch.fnmatch(basename, self.getConfigurationValue('pattern')):
                        filename = os.path.join(root, basename)
                        found_files.append(filename)
                if not self.getConfigurationValue('recursive'):
                    break
        return found_files

    def startFileTailer(self):
        self.file_tailer = []
        for file_to_tail in self.files: # (self, lumbermill_module, filename, callback, position="end", file_config=None):
            self.file_tailer.append(Tail(self, file_to_tail, self.handleFileChange))
            self.file_tailer[-1].start()

    def getStartMessage(self):
        return "Scanned %s. Found %d files." % (self.getConfigurationValue('paths'), self.total_file_count)

    def initAfterFork(self):
        """
        When running with multiple processes, calculate the the number of files each processes should work on.
        If dividing the number of files by the number of workers yields a remainder, master process will take care of it.
        """
        BaseThreadedModule.initAfterFork(self)
        datastore = self.lumbermill.getInternalDataStore()
        datastore.acquireLock()
        from_file_list_idx = datastore.getDataDict()[self.datastore_key]
        to_file_list_idx = from_file_list_idx + int(len(self.files) / self.lumbermill.getWorkerCount())
        if self.lumbermill.is_master():
            to_file_list_idx += len(self.files) % self.lumbermill.getWorkerCount()
        self.files = self.files[from_file_list_idx:to_file_list_idx]
        datastore.getDataDict()[self.datastore_key] = to_file_list_idx
        datastore.releaseLock()

    def handleFileChange(self, callback_data):
        while True:
            try:
                line = callback_data['lines'].popleft()
            except IndexError:
                break
            self.sendEvent(DictUtils.getDefaultEventDict(dict={"filename": callback_data['filename'], "data": line}, caller_class_name=self.__class__.__name__))

    def run(self):
        if self.mode == 'cat':
            for found_file in self.files:
                if not os.path.isfile(found_file):
                    self.logger.warning("File %s does not exist. Skipping." % found_file)
                    continue
                with open(found_file, 'r') as data_file:
                    if self.line_by_line:
                        for line in data_file:
                            self.sendEvent(DictUtils.getDefaultEventDict(dict={"filename": found_file, "data": line}, caller_class_name=self.__class__.__name__))
                    else:
                        self.sendEvent(DictUtils.getDefaultEventDict(dict={"filename": found_file, "data": data_file.read()}, caller_class_name=self.__class__.__name__))
            self.lumbermill.shutDown()
        elif self.mode == 'tail':
            self.startFileTailer()
            while self.alive:
                time.sleep(.01)
                pass

    def shutDown(self):
        if self.file_tailer:
            for file_tailer in self.file_tailer:
                file_tailer.close()
        self.alive = False