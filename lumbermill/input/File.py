# -*- coding: utf-8 -*-
import fnmatch
import os
import random
import types

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils import DictUtils
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class File(BaseThreadedModule):
    """

    Read data from files.

    paths:              An array of paths to scan for files.
    pattern:            Pattern the filenames need to match. E.g. '*.pdf', 'article*.xml' etc.
    recursive:          If set to true, scan paths recursively else only scan current dir.
    line_by_line:       If set to true, each line in a file will be emitted as single event.
                        If set to false, the whole file will be send as single event.

    Configuration template:

    - File:
       paths:                           # <type: string||list; is: required>
       pattern:                         # <default: '*'; type: string; is: optional>
       recursive:                       # <default: False; type: boolean; is: optional>
       line_by_line:                    # <default: False; type: boolean; is: optional>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
        # Call parent configure method.
        BaseThreadedModule.configure(self, configuration)
        paths = self.getConfigurationValue('paths')
        if isinstance(paths, types.StringType):
            paths = [paths]
        self.line_by_line = self.getConfigurationValue('line_by_line');
        self.files = []
        for path in paths:
            self.files += self.getFilesInPath(path,
                                              self.getConfigurationValue('pattern'),
                                              self.getConfigurationValue('recursive'))
        self.datastore_key = "%032x%s" % (random.getrandbits(128), self.process_id)
        self.total_file_count = len(self.files)
        self.lumbermill.setInInternalDataStore(self.datastore_key, 0)

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

    def getFilesInPath(self, path, pattern, recursive=False):
        if os.path.isfile(path):
            return [path]
        found_files = []
        for root, dirs, files in os.walk(path):
            for basename in files:
                if fnmatch.fnmatch(basename, pattern):
                    filename = os.path.join(root, basename)
                    found_files.append(filename)
            if not recursive:
                break
        return found_files

    def run(self):
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
