# -*- coding: utf-8 -*-
import struct
import sys
from socket import inet_ntoa
import re
import os

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class NetFlowParser(BaseThreadedModule):
    r"""
    Netflow parser

    Decode netflow packets.

    source_field:   Input field to decode.
    target_field:   Event field to be filled with the new data.

    Configuration template:

    - NetFlowParser:
       source_field:                    # <default: 'data'; type: string; is: optional>
       target_field:                    # <default: 'data'; type: string; is: optional>
       keep_original:                   # <default: False; type: boolean; is: optional>
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""

    NF_V5_HEADER_LENGTH = 24
    NF_V5_RECORD_LENGTH = 48

    TH_FIN = 0x01  # end of data
    TH_SYN = 0x02  # synchronize sequence numbers
    TH_RST = 0x04  # reset connection
    TH_PUSH = 0x08  # push
    TH_ACK = 0x10  # acknowledgment number set
    TH_URG = 0x20  # urgent pointer set
    TH_ECE = 0x40  # ECN echo, RFC 3168
    TH_CWR = 0x80  # congestion window reduced

    IP_PROTOCOLS = {}

    # Helper functions
    def readProtocolInfo(self):
        path = "%s/../assets/ip_protocols" % os.path.dirname(os.path.realpath(__file__))
        r = re.compile("(?P<proto>\S+)\s+(?P<num>\d+)")
        with open(path, 'r') as f:
            for line in f:
                m = r.match(line)
                if not m:
                    continue
                NetFlowParser.IP_PROTOCOLS[int(m.group("num"))] = m.group("proto")

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')
        self.target_field = self.getConfigurationValue('target_field')
        self.drop_original = not self.getConfigurationValue('keep_original')
        self.readProtocolInfo()

    def getTcpFflags(self, flags):
        ret = []
        if flags & NetFlowParser.TH_FIN:
                ret.append('FIN')
        if flags & NetFlowParser.TH_SYN:
                ret.append('SYN')
        if flags & NetFlowParser.TH_RST:
                ret.append('RST')
        if flags & NetFlowParser.TH_PUSH:
                ret.append('PUSH')
        if flags & NetFlowParser.TH_ACK:
                ret.append('ACk')
        if flags & NetFlowParser.TH_URG:
                ret.append('URG')
        if flags & NetFlowParser.TH_ECE:
                ret.append('ECE')
        if flags & NetFlowParser.TH_CWR:
                ret.append('CWR')
        return ret

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
            nf_data['tcp_flags_binary'] = decoded_record[9]
            nf_data['tcp_flags'] = self.getTcpFflags(decoded_record[9])
            nf_data['prot'] = decoded_record[10]
            nf_data['prot_name'] = NetFlowParser.IP_PROTOCOLS[decoded_record[10]]
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
        try:
            decoder_func = getattr(self, "decodeVersion%s" % version)
        except AttributeError:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Netflow parser does not implement decoder for netflow version: %s. Exception: %s, Error: %s" % (version, etype, evalue))
            self.lumbermill.shutDown()
        copy_event = False
        for netflow_data in decoder_func(raw_nf_data, record_count):
            if copy_event:
                event = event.copy()
            copy_event = True
            if self.drop_original and self.source_field is not self.target_field:
                event.pop(self.source_field, None)
            event.update({self.target_field: netflow_data})
            event['lumbermill']['event_type'] = "NetFlowV%s" % version
            yield event


