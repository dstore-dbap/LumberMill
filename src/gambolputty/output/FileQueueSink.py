# -*- coding: utf-8 -*-
import queuelib
import msgpack
import sys
import Utils
import BaseModule
from Decorators import ModuleDocstringParser

class BufferedFiFoWriteQueue():
    def __init__(self, queue, buffersize=100, interval=10):
        self.queue = queue
        self.buffer = Utils.Buffer(buffersize, self.sendBuffer, interval)

    def push(self, payload):
        self.buffer.append(payload)

    def sendBuffer(self, buffered_data):
        try:
            payload_ser = msgpack.packb(buffered_data)
            self.queue.push(payload_ser)
            return True
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not flush buffer. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))

    def pop(self):
        payload_ser = self.queue.pop()
        if not payload_ser:
            yield None
            return
        payload = msgpack.unpackb(payload_ser)
        for item in payload:
            yield item

    def get(self):
        raise NotImplementedError

    def close(self):
        self.buffer.flush()
        self.queue.close()

    def __getattr__(self, name):
        return getattr(self.queue, name)

@ModuleDocstringParser
class FileQueueSink(BaseModule.BaseModule):
    """
    Stores all received events in a file based queue for persistance.

    path: Path to queue file.
    store_interval_in_secs: sending data to es in x seconds intervals.
    batch_size: sending data to es if event count is above, even if store_interval_in_secs is not reached.

    - FileQueueSink:
        path:                           # <type: string; is: required>
        store_interval_in_secs:         # <default: 10; type: integer; is: optional>
        batch_size:                     # <default: 500; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""
    can_run_parallel = False

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        try:
           queue = queuelib.FifoDiskQueue(self.getConfigurationValue("path"))
           self.buffered_queue = BufferedFiFoWriteQueue(queue, buffersize=100, interval=10)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sFailed to create queue file in %s. Exception: %s, Error: %s%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue("queuefile"), etype, evalue, Utils.AnsiColors.ENDC))
            self.gp.shutDown()

    def handleEvent(self, event):
        self.buffered_queue.push(event)
        yield None