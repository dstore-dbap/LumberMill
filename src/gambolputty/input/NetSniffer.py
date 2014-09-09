# -*- coding: utf-8 -*-
import os
import platform
import csv
import logging
import re
import socket
import sys
import struct
import Utils
import BaseThreadedModule
from Decorators import ModuleDocstringParser

ETH_P_ALL = 3
ETH_PROTOCOLS = {'0x8': 'IPv4'}
IPV4_PROTOCOLS = {'0x6': 'TCP'}

@ModuleDocstringParser
class NetSniffer(BaseThreadedModule.BaseThreadedModule):
    """
    Sniff network traffic. Needs root privileges.

    eth_protocols: At the moment only IPv4 is supported (@see: http://en.wikipedia.org/wiki/EtherType).

    Configuration example:

    - TcpSniffer:
        interface:          # <type: None||string; default: None; is: optional>
        eth_protocols:      # <type: list; default: ['0x8']; is: optional>
        ip_protocols:       # <type: list; default: ['0x6']; is: optional>
        tcp_protocols:      # <type: list; default: [80]; is: optional>
        source_ips:         # <type: None||list; default: None; is: optional>
        destination_ips:    # <type: None||list; default: None; is: optional>
        promiscous:         # <type: boolean; default: False; is: optional>
        receivers:
          - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = False

    def configure(self, configuration):
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.interface = self.getConfigurationValue('interface')
        self.eth_protocols = self.getConfigurationValue('eth_protocols')
        self.ip_protocols = self.getConfigurationValue('ip_protocols')
        self.tcp_protocols = self.getConfigurationValue('tcp_protocols')
        self.promiscous_mode = self.getConfigurationValue('promiscous')
        self.packet_decoders = {}
        for ether_type, ether_protocol in ETH_PROTOCOLS.items():
            if "decodePacket%s" % ether_protocol in dir(self):
                self.packet_decoders[ether_type] = getattr(self, "decodePacket%s" % ether_protocol)
                if ether_protocol not in NetSniffer.ENCAPSULATED_PROTOCOLS:
                    continue
                for enc_protocol_type, enc_protocol in NetSniffer.ENCAPSULATED_PROTOCOLS[ether_protocol].items():
                    if "decodePacket%s%s" % (ether_protocol,enc_protocol) in dir(self):
                        self.packet_decoders[enc_protocol_type] = getattr(self, "decodePacket%s%s" % (ether_protocol,enc_protocol))
        try:
            if Utils.MY_SYSTEM_NAME == 'Linux':
                self.sniffer_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
                self.sniffer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**30)
            else:
                self.sniffer_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sSniffersocket could not be created. Exception: %s, Error: %s.%s" %(Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))
            self.gp.shutDown()
        try:
            if self.promiscous_mode:
                if Utils.MY_SYSTEM_NAME == 'Windows':
                    self.sniffer_socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
                else:
                    os.system('ifconfig %s promisc' % self.interface)
                    #os.system("ip link set %s promisc on" % self.interface)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not enable promiscous mode on %s. Exception: %s, Error: %s.%s" %(Utils.AnsiColors.FAIL, self.interface, etype, evalue, Utils.AnsiColors.ENDC))
            self.gp.shutDown()

    def getPacketDecoder(self, packet_protocol):
        if packet_protocol not in ETH_PROTOCOLS:
            return None
        try:
            return self.packet_decoders[packet_protocol]
        except KeyError:
            # Try to find a matching decoder.
            protocol_name = ETH_PROTOCOLS[packet_protocol]
            try:
                packet_decoder_name = 'PacketDecoder%s' % protocol_name
                self.packet_decoders[packet_protocol] = globals()[packet_decoder_name](self.ip_protocols)
                return self.packet_decoders[packet_protocol]
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sCould not find packet decoder for protocol %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, protocol_name, etype, evalue, Utils.AnsiColors.ENDC))
                return None

    def decodePacket(self, packet_protocol, packet):
        decoder = self.getPacketDecoder(packet_protocol)
        if not decoder:
            return packet
        return decoder.decodePacket(packet)

    def readTcpServiceInfo(self):
        path_to_csv_file = "%s/../assets/tcp_services.csv" % os.path.dirname(os.path.realpath(__file__))
        with open(path_to_csv_file, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=':')
            for row in reader:
                pass

    def run(self):
        # With pypy 2.x this throws <error: unknown address family>
        if self.interface and Utils.MY_SYSTEM_NAME == 'Linux' and not Utils.is_pypy:
            self.sniffer_socket.bind((self.interface, ETH_P_ALL))
        elif Utils.MY_SYSTEM_NAME != 'Linux':
            host = socket.gethostbyname(Utils.MY_HOSTNAME)
            self.sniffer_socket.bind((host, 0))
        while self.alive:
            packet, packet_address_data = self.sniffer_socket.recvfrom(65565)
            # TODO: Support more ethernet protocols than just IPv4 for windows and mac.
            packet_protocol = '0x8'
            decoded_packet = Utils.getDefaultEventDict({'protocols': ['ethernet'], 'data': packet[14:]}, caller_class_name=self.__class__.__name__)
            if Utils.MY_SYSTEM_NAME == 'Linux':
                eth_header = struct.unpack("!6s6sH", packet[0:14])
                packet_protocol = hex(socket.ntohs(eth_header[2]))
                if packet_protocol not in self.eth_protocols:
                    continue
                decoded_packet['direction'] = 'outgoing' if packet_address_data[2] == socket.PACKET_OUTGOING else 'incoming'
            decoded_packet = self.decodePacket(packet_protocol, decoded_packet)
            if not decoded_packet['data']:
                continue
            if self.tcp_protocols and \
                    (('TCP' not in decoded_packet['protocols']) \
                        or \
                    (decoded_packet['source_port'] not in self.tcp_protocols and decoded_packet['destination_port'] not in self.tcp_protocols)):
                continue
            self.sendEvent(decoded_packet)

    def shutDown(self):
        if self.promiscous_mode:
            if platform.system() == 'Windows':
                self.sniffer_socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
            else:
                os.system('ifconfig %s -promisc' % self.interface)
                #os.system("ip link set %s promisc off" % self.interface)

class BasePacketDecoder:

    def __init__(self, protocol_filter):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.protocol_filter = protocol_filter
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
                self.packet_decoders[packet_protocol] = globals()[packet_decoder_name]({})
                return self.packet_decoders[packet_protocol]
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sCould not find packet decoder for protocol %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, protocol_name, etype, evalue, Utils.AnsiColors.ENDC))
                return None


class PacketDecoderIPv4(BasePacketDecoder):

    def __init__(self, protocol_filter=None):
        BasePacketDecoder.__init__(self, protocol_filter)
        self.known_protocols = {'0x6': 'TCP'}

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
        s_addr = socket.inet_ntoa(ip_header[8]);
        d_addr = socket.inet_ntoa(ip_header[9]);
        packet['protocols'].append('IPv4')
        packet.update({'version': version,
                       'ttl': ttl,
                       'source': s_addr,
                       'destination': d_addr,
                       'data': packet_data[ip_header_length:]})
        if not self.protocol_filter or (ip_protocol in self.protocol_filter):
            decoder = self.getPacketDecoder(ip_protocol)
            if decoder:
                packet = decoder.decodePacket(packet)
        return packet

class PacketDecoderTCP(BasePacketDecoder):

    def __init__(self, protocol_filter=None):
        BasePacketDecoder.__init__(self, protocol_filter)
        self.known_protocols = {23: 'TELNET',
                                25: 'POP',
                                80: 'HTTP',
                                143: 'IMAP'}
        self.ctrl_flags = {'fin': 1, 'syn': 2, 'rst': 4, 'psh': 8, 'ack': 16, 'urg': 32}

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
        tcp_protocol = dest_port if packet['direction'] == 'outgoing' else source_port
        packet.update({'source_port': source_port,
                       'destination_port': dest_port,
                       'sequence_number': sequence,
                       'ack': acknowledgement,
                       'data': packet_data[data_offset:]})
        if not self.protocol_filter or (tcp_protocol in self.protocol_filter):
            decoder = self.getPacketDecoder(tcp_protocol)
            if decoder:
                packet = decoder.decodePacket(packet)
        return packet

class PacketDecoderTELNET(BasePacketDecoder):

    def decodePacket(self, packet):
        packet['protocols'].append('telnet')
        return packet

class PacketDecoderHTTP(BasePacketDecoder):

    def __init__(self, protocol_filter=None):
        BasePacketDecoder.__init__(self, protocol_filter)
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

class PacketDecoderPOP(BasePacketDecoder):

    def decodePacket(self, packet):
        packet['protocols'].append('pop')
        return packet

class PacketDecoderIMAP(BasePacketDecoder):

    def decodePacket(self, packet):
        packet['protocols'].append('imap')
        return packet