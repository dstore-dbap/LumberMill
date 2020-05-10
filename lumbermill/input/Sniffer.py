# -*- coding: utf-8 -*-
import logging
import re
import socket
import struct
import sys

import pcapy
from impacket.ImpactDecoder import EthDecoder

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser

PROTOCOL_TO_NAMES = {'eth': 'Ethernet',
                     '0x800': 'IPv4'}
"""
<class 'impacket.ImpactPacket.TCP'>
<class 'impacket.ImpactPacket.Data'>
<class 'impacket.ImpactPacket.ARP'>
"""

@ModuleDocstringParser
class Sniffer(BaseThreadedModule):
    """
    Sniff network traffic. Needs root privileges.

    Reason for using pcapy as sniffer lib:
    As LumberMill is intended to be run with pypy, every module should be compatible with pypy.
    Creating a raw socket in pypy is no problem but it is (up to now) not possible to bind this
    socket to a selected interface, e.g. socket.bind(('lo', 0)) will throw "error: unknown address family".
    With pcapy this problem does not exist.

    Dependencies:
     - pcapy, impacket: pypy -m pip install pcapy impacket
     - libpcap-dev

    Configuration template:

    - input.Sniffer:
       interface:                       # <default: 'any'; type: None||string; is: optional>
       protocols:                       # <default: ['Data']; type: list; is: optional>
       packetfilter:                    # <default: None; type: None||string; is: optional>
       promiscous:                      # <default: False; type: boolean; is: optional>
       target_field:                    # # <default: None; type: None||string; is: optional>
       key_value_store:                 # <default: None; type: none||string; is: optional>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = False

    def configure(self, configuration):
        BaseThreadedModule.configure(self, configuration)
        self.interface = self.getConfigurationValue('interface')
        self.protocols = self.getConfigurationValue('protocols')
        self.promiscous_mode = 1 if self.getConfigurationValue('promiscous') else 0
        self.target_field = self.getConfigurationValue('target_field')
        self.kv_store = self.getConfigurationValue('key_value_store') if self.getConfigurationValue('key_value_store') else {}
        self.packet_decoders = {}
        try:
            self.sniffer = pcapy.open_live(self.interface, 65536, self.promiscous_mode, 100)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Sniffer could not be created. Exception: %s, Error: %s." % (etype, evalue))
            self.lumbermill.shutDown()
        if self.getConfigurationValue('packetfilter'):
            self.sniffer.setfilter(self.getConfigurationValue('packetfilter'))
        self.link_layer = self.sniffer.datalink()

    def getStartMessage(self):
        start_msg = "sniffing %s on %s. Filter: %s." % (self.protocols, self.interface, self.getConfigurationValue('packetfilter'))
        return start_msg

    def getPacketDecoder(self, packet_protocol):
        try:
            return self.packet_decoders[packet_protocol]
        except KeyError:
            # Try to find a matching decoder.
            protocol_name = PROTOCOL_TO_NAMES[packet_protocol]
            try:
                packet_decoder_name = 'PacketDecoder%s' % protocol_name
                self.packet_decoders[packet_protocol] = globals()[packet_decoder_name]()
                return self.packet_decoders[packet_protocol]
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not find packet decoder for protocol %s. Exception: %s, Error: %s." % (protocol_name, etype, evalue))
                return None

    def decodePacket(self, packet, packet_protocol):
        decoder = self.getPacketDecoder(packet_protocol)
        if not decoder:
            return packet
        return decoder.decodePacket(packet)

    def run(self):
        while self.alive:
            packet = None
            try:
                pcap_header, packet = self.sniffer.next()
            except:
                pass
            if not packet:
                continue
            decoder = self.getPacketDecoder('eth')
            if not decoder:
                continue
            decoded_data = {'protocols': []}
            for decoded_packet in decoder.decodePacket(packet):
                packet_type = str(type(decoded_packet))
                if packet_type == "<class 'impacket.ImpactPacket.Ethernet'>":
                    self.parseEtherPacket(decoded_packet, decoded_data)
                elif packet_type == "<class 'impacket.ImpactPacket.IP'>":
                    self.parseIPPacketEvent(decoded_packet, decoded_data)
                elif packet_type == "<class 'impacket.ImpactPacket.TCP'>":
                    self.parseTCPPacketEvent(decoded_packet, decoded_data)
                elif packet_type == "<class 'impacket.ImpactPacket.Data'>":
                    self.parseDataPacketEvent(decoded_packet, decoded_data)
            if decoded_data['data']:
                event = DictUtils.getDefaultEventDict(caller_class_name=self.__class__.__name__)
                if self.target_field:
                    event[self.target_field] = decoded_data
                else:
                    event.update(decoded_data)
                self.sendEvent(event)

    def parseEtherPacket(self, decoded_packet, event):
        event['protocols'].append('ethernet')
        event['packet_size'] = decoded_packet.get_size()
        event['data'] = decoded_packet.get_data_as_string()
        event['source_mac'] = decoded_packet.as_eth_addr(decoded_packet.get_ether_shost())
        event['destination_mac'] = decoded_packet.as_eth_addr(decoded_packet.get_ether_dhost())

    def parseIPPacketEvent(self, decoded_packet, event):
        event['protocols'].append('IPv4')
        event['packet_size'] = decoded_packet.get_size()
        event['data'] = decoded_packet.get_data_as_string()
        event['ethertype'] = hex(decoded_packet.ethertype)
        event['s_ip'] = decoded_packet.get_ip_src()
        event['d_ip'] = decoded_packet.get_ip_dst()

    def parseTCPPacketEvent(self, decoded_packet, event):
        event['protocols'].append('TCP')
        event['packet_size'] = decoded_packet.get_size()
        event['s_port'] = decoded_packet.get_th_sport()
        event['d_port'] = decoded_packet.get_th_dport()

    def parseDataPacketEvent(self, decoded_packet, event):
        event['data'] = decoded_packet.get_bytes().tostring()
        #if data:
        #    event['data'] = data;


class PacketDecoderEthernet:
    def __init__(self):
        self.decoder = EthDecoder()

    def decodePacket(self, packet):
        packet = self.decoder.decode(packet)
        while packet:
            yield packet
            packet = packet.child()

###
# We use impacket now, so no need to decode ourselfs.
###
class BasePacketDecoder:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.packet_decoders = {}
        self.known_protocols = {}

    def getPacketDecoder(self, packet_protocol):
        if packet_protocol not in self.known_protocols:
            return None
        try:
            return self.packet_decoders[packet_protocol]
        except KeyError:
            # Try to find a matching decoder.
            protocol_name = self.known_protocols[packet_protocol]
            try:
                packet_decoder_name = 'PacketDecoder%s' % protocol_name
                self.packet_decoders[packet_protocol] = globals()[packet_decoder_name]()
                return self.packet_decoders[packet_protocol]
            except:
                #etype, evalue, etb = sys.exc_info()
                #self.logger.error("Could not find packet decoder for protocol %s. Exception: %s, Error: %s." % (protocol_name, etype, evalue))
                return None

class PacketDecoderIPv4(BasePacketDecoder):

    PROTOCOLS = {'0x6': 'TCP'}

    def __init__(self):
        BasePacketDecoder.__init__(self)
        self.known_protocols = PacketDecoderIPv4.PROTOCOLS

    def decodePacket(self, packet):
        """Decode an IPv4 packet. See http://en.wikipedia.org/wiki/IPv4"""
        packet_data = packet['data']
        ip_header = struct.unpack('!BBHHHBBH4s4s' , packet_data[0:20])
        version_ihl = ip_header[0]
        version = version_ihl >> 4
        ihl = version_ihl & 0xF
        ip_header_length = ihl * 4
        ttl = ip_header[5]
        ip_protocol = hex(ip_header[6])
        s_addr = socket.inet_ntoa(ip_header[8])
        d_addr = socket.inet_ntoa(ip_header[9])
        packet['protocols'].append('IPv4')
        packet.update({'version': version,
                       'ttl': ttl,
                       'source': s_addr,
                       'destination': d_addr,
                       'data': packet_data[ip_header_length:]})
        decoder = self.getPacketDecoder(ip_protocol)
        if decoder:
            packet = decoder.decodePacket(packet)
        return packet

class PacketDecoderTCP(BasePacketDecoder):

    PROTOCOLS = {
        1: 'TCPMUX',
        5: 'RJE',
        7: 'ECHO',
        9: 'DISCARD',
        11: 'SYSTAT',
        13: 'DAYTIME',
        17: 'QOTD',
        18: 'MSP',
        19: 'CHARGEN',
        20: 'FTP-DATA',
        21: 'FTP',
        22: 'SSH',
        23: 'TELNET',
        24: 'LMTP',
        25: 'SMTP',
        37: 'TIME',
        39: 'RLP',
        42: 'NAMESERVER',
        43: 'NICNAME',
        49: 'TACACS',
        50: 'RE-MAIL-CK',
        53: 'DOMAIN',
        63: 'WHOIS++',
        67: 'BOOTPS',
        68: 'BOOTPC',
        69: 'TFTP',
        70: 'GOPHER',
        71: 'NETRJS-1',
        72: 'NETRJS-2',
        73: 'NETRJS-3',
        74: 'NETRJS-4',
        79: 'FINGER',
        80: 'HTTP',
        88: 'KERBEROS',
        95: 'SUPDUP',
        101: 'HOSTNAME',
        102: 'ISO-TSAP',
        105: 'CSNET-NS',
        107: 'RTELNET',
        109: 'POP2',
        110: 'POP3',
        111: 'SUNRPC',
        113: 'AUTH',
        115: 'SFTP',
        117: 'UUCP-PATH',
        119: 'NNTP',
        123: 'NTP',
        137: 'NETBIOS-NS',
        138: 'NETBIOS-DGM',
        139: 'NETBIOS-SSN',
        143: 'IMAP',
        161: 'SNMP',
        162: 'SNMPTRAP',
        163: 'CMIP-MAN',
        164: 'CMIP-AGENT',
        174: 'MAILQ',
        177: 'XDMCP',
        178: 'NEXTSTEP',
        179: 'BGP',
        191: 'PROSPERO',
        194: 'IRC',
        199: 'SMUX',
        201: 'AT-RTMP',
        202: 'AT-NBP',
        204: 'AT-ECHO',
        206: 'AT-ZIS',
        209: 'QMTP',
        210: 'Z39.50',
        213: 'IPX',
        220: 'IMAP3',
        245: 'LINK',
        347: 'FATSERV',
        363: 'RSVP_TUNNEL',
        366: 'ODMR',
        369: 'RPC2PORTMAP',
        370: 'CODAAUTH2',
        372: 'ULISTPROC',
        389: 'LDAP',
        400: 'OSB-SD',
        427: 'SVRLOC',
        434: 'MOBILEIP-AGENT',
        435: 'MOBILIP-MN',
        443: 'HTTPS',
        444: 'SNPP',
        445: 'MICROSOFT-DS',
        464: 'KPASSWD',
        468: 'PHOTURIS',
        487: 'SAFT',
        488: 'GSS-HTTP',
        496: 'PIM-RP-DISC',
        500: 'ISAKMP',
        538: 'GDOMAP',
        535: 'IIOP',
        546: 'DHCPV6-CLIENT',
        547: 'DHCPV6-SERVER',
        554: 'RTSP',
        563: 'NNTPS',
        565: 'WHOAMI',
        587: 'SUBMISSION',
        610: 'NPMP-LOCAL',
        611: 'NPMP-GUI',
        612: 'HMMP-IND',
        631: 'IPP',
        636: 'LDAPS',
        674: 'ACAP',
        694: 'HA-CLUSTER',
        749: 'KERBEROS-ADM',
        750: 'KERBEROS-IV',
        765: 'WEBSTER',
        767: 'PHONEBOOK',
        873: 'RSYNC',
        875: 'RQUOTAD',
        992: 'TELNETS',
        993: 'IMAPS',
        994: 'IRCS',
        995: 'POP3S',
        512: 'EXEC',
        513: 'LOGIN',
        514: 'SHELL',
        515: 'PRINTER',
        519: 'UTIME',
        520: 'EFS',
        521: 'RIPNG',
        525: 'TIMED',
        526: 'TEMPO',
        530: 'COURIER',
        531: 'CONFERENCE',
        532: 'NETNEWS',
        540: 'UUCP',
        543: 'KLOGIN',
        544: 'KSHELL',
        548: 'AFPOVERTCP',
        1080: 'SOCKS'
    }

    def __init__(self):
        BasePacketDecoder.__init__(self)
        self.known_protocols = PacketDecoderTCP.PROTOCOLS
        self.ctrl_flags = {'fin': 1, 'syn': 2, 'rst': 4, 'psh': 8, 'ack': 16, 'urg': 32}
        self.flows = {}

    def decodePacket(self, packet):
        packet_data = packet['data']
        tcp_header = packet_data[0:20]
        tcph = struct.unpack('!HHLLHHHH' , tcp_header) #'!HHLLBBHHH'
        source_port = tcph[0]
        dest_port = tcph[1]
        sequence = tcph[2]
        acknowledgement = tcph[3]
        data_offset_reserved = tcph[4]
        data_offset = data_offset_reserved >> 12
        data_offset = data_offset * 4
        packet_ctrl_flags = data_offset_reserved & 0x3f
        packet['tcp_ctrl_flags'] = []
        for tcp_flag_name, tcp_flag_mask in self.ctrl_flags.items():
            if packet_ctrl_flags & tcp_flag_mask == tcp_flag_mask:
               packet['tcp_ctrl_flags'].append(tcp_flag_name)
        packet['protocols'].append('TCP')
        packet.update({'source_port': source_port,
                       'destination_port': dest_port,
                       'sequence_number': sequence,
                       'ack': acknowledgement,
                       'data': packet_data[data_offset:]})
        # Set flow id.
        flow_id = "%s %s" % tuple(sorted([ "%(source)s:%(source_port)s" % packet, "%(destination)s:%(destination_port)s" % packet ]))
        packet['flow_id'] = flow_id
        # Get protocol.
        tcp_protocol = None
        decoder = None
        if flow_id in self.flows:
            tcp_protocol = self.flows[flow_id]
        if packet['tcp_ctrl_flags'] in (['syn'], ['ack']) and flow_id not in self.flows:
            tcp_protocol = self.flows[flow_id] = dest_port
        elif packet['tcp_ctrl_flags'] in (['fin'], ['rst']) and flow_id in self.flows:
            del self.flows[flow_id]
        if tcp_protocol:
            decoder = self.getPacketDecoder(tcp_protocol)
        if decoder:
            packet = decoder.decodePacket(packet)
        # If no decoder was found at least set protocol name.
        elif tcp_protocol in self.known_protocols:
            packet['protocols'].append(self.known_protocols[tcp_protocol])
        return packet

class PacketDecoderHTTP(BasePacketDecoder):

    def __init__(self):
        BasePacketDecoder.__init__(self)
        self.re_request = re.compile(r"^(?P<http_method>\w+?)\s+(?P<url>.*?)\s+HTTP/[\d\.]+")
        self.re_headers = re.compile(r"^(?P<http_header>.*?): (?P<value>.*?)\r\n", re.MULTILINE)

    def decodePacket(self, packet):
        packet['protocols'].append('html')
        rawrequest = self.re_request.search(packet['data'])
        if rawrequest:
            packet.update(rawrequest.groupdict())
        headers = self.re_headers.findall(packet['data'])
        packet.update({header: value for header, value in headers})
        return packet
