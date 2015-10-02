# -*- coding: utf-8 -*-
import struct
from socket import inet_ntoa
import BaseThreadedModule
import Decorators


@Decorators.ModuleDocstringParser
class NetFlowParser(BaseThreadedModule.BaseThreadedModule):
    r"""
    Netflow parser

    Decode netflow packets.

    source_field:   Input field to decode.
    target_field:   Event field to be filled with the new data.

    Configuration template:

    - NetFlowParser:
        source_field:                         # <default: 'data'; type: string; is: optional>
        target_field:                         # <default: 'data'; type: string; is: optional>
        keep_original:                        # <default: False; type: boolean; is: optional>
        receivers:
          - NextModule
    """

    module_type = "parser"
    """Set module type"""

    NF_V5_HEADER_LENGTH = 24
    NF_V5_RECORD_LENGTH = 48

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')
        self.target_field = self.getConfigurationValue('target_field')
        self.drop_original = not self.getConfigurationValue('keep_original')

    def decodeVersion5(self, raw_nf_data, record_count):
        nf_data = {}
        (nf_data['sys_uptime'], nf_data['unix_secs'], nf_data['unix_nsecs'], nf_data['flow_sequence'], nf_data['engine_type'], nf_data['engine_id'], nf_data['sampling_interval']) = struct.unpack('!IIIIBBH', raw_nf_data[4:24])
        for i in xrange(0, record_count):
            record_starts_at = NetFlowParser.NF_V5_HEADER_LENGTH + (i * NetFlowParser.NF_V5_RECORD_LENGTH)
            record = raw_nf_data[record_starts_at:record_starts_at+NetFlowParser.NF_V5_RECORD_LENGTH]
            # Decode record, except src and dest addresses.
            decoded_record = struct.unpack('!HHIIIIHHBBBBHHBBH', record[12:])
            nf_data['srcaddr'] = inet_ntoa(record[:4])
            nf_data['dstaddr'] = inet_ntoa(record[4:8])
            nf_data['nexthop'] = inet_ntoa(record[8:12])
            nf_data['snmp_index_in_interface'] = decoded_record[0]
            nf_data['snmp_index_out_interface'] = decoded_record[1]
            nf_data['packet_count'] = decoded_record[2]
            nf_data['byte_count'] = decoded_record[3]
            nf_data['uptime_start'] = decoded_record[4]
            nf_data['uptime_end'] = decoded_record[5]
            nf_data['srcport'] = decoded_record[6]
            nf_data['dstport'] = decoded_record[7]
            nf_data['tcp_flags'] = decoded_record[9]
            nf_data['prot'] = decoded_record[10]
            nf_data['tos'] = decoded_record[11]
            nf_data['src_as'] = decoded_record[12]
            nf_data['dst_as'] = decoded_record[13]
            nf_data['src_mask'] = decoded_record[14]
            nf_data['dst_mask'] = decoded_record[15]
            yield nf_data

    def handleEvent(self, event):
        if self.source_field not in event:
            yield event
            return
        raw_nf_data = event[self.source_field]
        # Try to get netflow version.
        try:
             (version, record_count) = struct.unpack('!HH', raw_nf_data[0:4])
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not detect netflow version: %s. Exception: %s, Error: %s." % (raw_nf_data, etype, evalue))
            yield event
        # Call decoder for detected version.
        decoded_netflow_data = None
        try:
            copy_event = False
            for netflow_data in getattr(self, "decodeVersion%s" % version)(raw_nf_data, record_count):
                if copy_event:
                    event = event.copy()
                copy_event = True
                if self.drop_original and self.source_field is not self.target_field:
                    event.pop(self.source_field, None)
                event.update({self.target_field: netflow_data})
                yield event
        except AttributeError:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Netflow parser does not implement decoder for netflow version: %s. Exception: %s, Error: %s" % (version, etype, evalue))
            self.gp.shutDown()

