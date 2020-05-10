# -*- coding: utf-8 -*-
import sys
import msgpack

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class MsgPack(BaseThreadedModule):
    """
    Decode:
     It will parse the msgpack data and create or replace fields in the internal data dictionary with
     the corresponding json fields.
    Encode:
     Encode selected fields or all to msgpack format.

    Configuration template:

    - parser.MsgPack:
       action:                          # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
       mode:                            # <default: 'line'; type: string; values: ['line','stream']; is: optional>
       source_fields:                   # <default: 'data'; type: string||list; is: optional>
       target_field:                    # <default: None; type: None||string; is: required if action is 'encode' or keep_original is False else optional>
       keep_original:                   # <default: False; type: boolean; is: optional>
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_fields = self.getConfigurationValue('source_fields')
        # Allow single string as well.
        if isinstance(self.source_fields, str):
            self.source_fields = [self.source_fields]
        self.target_field = self.getConfigurationValue('target_field')
        self.drop_original = not self.getConfigurationValue('keep_original')
        if self.drop_original and not self.target_field:
            self.logger.error("Module configured to drop original field after decoding but no target field set. Please either set target_field or set keep_original to True.")
            self.lumbermill.shutDown()
        if self.getConfigurationValue('action') == 'decode':
            if self.getConfigurationValue('mode') == 'line':
                self.handleEvent = self.decodeEventLine
            else:
                self.logger.warning("Stream mode is currently broken. Sorry!")
                self.lumbermill.shutDown()
                self.unpacker = msgpack.Unpacker(raw=False)
                self.handleEvent = self.decodeEventStream
        else:
            self.handleEvent = self.encodeEvent

    def decodeEventStream(self, event):
        for source_field in self.source_fields:
            try:
                data = event[source_field]
            except KeyError:
                continue
            try:
                self.unpacker.feed(data)
            except TypeError:
                try:
                    self.unpacker.feed(bytes(data, "utf-8"))
                except TypeError:
                    continue;
            # If decoded data contains more than one event, we need to clone all events but the first one.
            # Otherwise we will have multiple events with the same event_id.
            # KeyDotNotationDict.copy method will take care of creating a new event id.
            for events_count, decoded_data in enumerate(self.unpacker):
                if events_count > 1:
                    event = event.copy()
                if not isinstance(decoded_data, dict):
                    continue
                if self.drop_original:
                    event.pop(source_field, None)
                if self.target_field:
                    event[self.target_field] = decoded_data
                else:
                    try:
                        event.update(decoded_data)
                    except:
                        etype, evalue, etb = sys.exc_info()
                        self.logger.warning("Could not update event with msgpack data: %s. Exception: %s, Error: %s." % (decoded_data, etype, evalue))
                yield event

    def decodeEventLine(self, event):
        for source_field in self.source_fields:
            try:
                decoded_data = msgpack.unpackb(event[source_field], raw=False)
            except KeyError:
                continue
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Could not parse msgpack event data: %s. Exception: %s, Error: %s." % (event[source_field], etype, evalue))
                continue
            if self.drop_original:
                event.pop(source_field, None)
            if self.target_field:
                event.update({self.target_field: decoded_data})
            else:
                try:
                    event.update(decoded_data)
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.warning("Could not update event with msgpack data: %s. Exception: %s, Error: %s." % (decoded_data, etype, evalue))
        yield event

    def encodeEvent(self, event):
        if self.source_fields == ['all']:
            encode_data = event
        else:
            encode_data = {}
            for source_field in self.source_fields:
                try:
                    encode_data[source_field] = event[source_field]
                except KeyError:
                    continue
                if self.drop_original:
                    event.pop(source_field, None)
        try:
            encode_data = msgpack.packb(encode_data)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not msgpack encode event data: %s. Exception: %s, Error: %s." % (event, etype, evalue))
            yield event
            return
        if self.source_fields == ['all']:
            event = encode_data
        else:
            event.update({self.target_field: encode_data})
        yield event
