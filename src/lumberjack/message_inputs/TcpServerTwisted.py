#!/usr/bin/python
# -*- coding: UTF-8 -*-
########################################################
# A simple implementation of a syslog server
# Example usage:
# syslogd = TwistedTcpServer()
# syslogd.registerUDPListener(UPDListener())
# syslogd.startRegisterdListeners()
#
#    syslogDaemon = TcpServerTwisted()
#    syslogTCP = handlerFactory()
#    syslogTCP.setOutputQueues(Queue.Queue())
#    syslogDaemon.registerTCPListener(syslogTCP)
#    syslogDaemon.startRegisterdListeners()
########################################################
import sys
import os
import logging
import socket
import BaseModule
from twisted.internet import defer, reactor, protocol, threads
from twisted.protocols.basic import LineReceiver

LOG_PRIMASK = 0x07
PRIMASK = { 
0 : "emerg", 
1 : "alert",
2 : "crit",
3 : "err",
4 : "warning",
5 : "notice",
6 : "info",
7 : "debug"
}

FACILITYMASK = {
      0  : "kern",
      1  : "user",
      2  : "mail",
      3  : "daemon",
      4  : "auth",
      5  : "syslog",
      6  : "lpr",
      7  : "news",
      8  : "uucp",
      9  : "cron",
      10 : "authpriv",
      11 : "ftp",
      12 : "ntp",
      13 : "security",
      14 : "console",
      15 : "mark",
      16 : "local0",
      17 : "local1",
      18 : "local2",
      19 : "local3",
      20 : "local4",
      21 : "local5",
      22 : "local6",
      23 : "local7",
}

def bit2string(number):
    try: return "%s.%s"%(FACILITYMASK[number>>3] , PRIMASK[number & LOG_PRIMASK])
    except: return #return "unknown.unknown"
        

class UPDListener(protocol.DatagramProtocol):
    
    def doStart(self):
        print ""

    def setDatagramHandler(self, handlerObjects):
        """
        If a handler object is set all received datagrams will be send 
        to a callback method <handlerObject.handleDatagram(data)>
        If no handleObject is passed, data will be printed out to stdout.
        """
        self.receivers = handlerObjects     
    
    def datagramReceived(self, data, (ip, port)):
        other = ""
        if data.index(">") < 4:
            try:
                other = ip+bit2string(int(data[data.index("<"):data.index(">")]))
            except:
                other = ip
        else:
            other = ip
        data = other + " " + data[data.index(">")+1:] + "\n"
        for handler in self.receivers:
            handler.handleData(data)

class TCPListener(LineReceiver):
    delimiter = '\n'
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.counter = 0
    
    def __connectionMade(self):
        self.factory.numberConnections += 1
        if self.factory.numberConnections > self.factory.maxNumberConnections:
            self.logger.info("maxNumberConnections exceeded. Dropping connection.")
            self.transport.loseConnection()

    def lineReceived(self, data):
        try:
            host = self.transport.getPeer().host;
        except:
            host = "0.0.0.0"
        try:
            [queue.put({"received_from": host, "data": data}, block=True, timeout=5) for queue in self.factory.output_queues]
        except Exception, e:
            self.logger.error("Could not add received data to output queue. Excpeption: %s, Error: %s." % (Exception, e))

class handlerFactory(protocol.Factory):
    protocol = TCPListener
    numberConnections = 0
    maxNumberConnections = 4096
    output_queues = []

    def setOutputQueues(self, queues):
        self.output_queues = queues

class TcpServerTwisted(BaseModule.BaseModule):
    """
    A simple implematation of a syslog server
    """
    udpListener = None
    tcpListener = None

    def registerUDPListener(self, udpListenerObject):
        self.udpListener = udpListenerObject
        
    def registerTCPListener(self, tcpListenerObject):
        self.tcpListener = tcpListenerObject

    def startRegisterdListeners(self):
        start_reactor = False
        if isinstance(self.udpListener, protocol.DatagramProtocol):
            self.logger.info("Starting TwistedUdpServer on interface %s, port: %s" % (self.config["Interface"],self.config["UDP"]))
            try:
                reactor.listenUDP(int(self.config["UDP"]), self.udpListener, self.config["Interface"],self.config["UDP"])
            except Exception, e:
                self.logger.error("An error occured: Exception: %s, Error: %s." % (Exception,e))
                self.logger.info("No UDPListener registered...")
                sys.exit(255)
            start_reactor = True
        if(isinstance(self.tcpListener, protocol.Factory)):
            self.logger.info("Starting TwistedTcpServer on interface %s, port: %s" % (self.config["Interface"],self.config["TCP"]))
            try:
                server = reactor.listenTCP(int(self.config["TCP"]), self.tcpListener, interface = self.config["Interface"])
                server.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                server.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
            except Exception, e:
                self.logger.error("An error occured: Exception: %s, Error: %s." % (Exception,e))
                self.logger.error("No TCPListener registered...")
                sys.exit(255)
            start_reactor = True
        if start_reactor:
            reactor.run(installSignalHandlers=False)
        else:
            self.logger.info("No Listeners registered. Not starting...")

    def run(self):
        if not self.output_queues:
            self.logger.warning("Will not start module %s since no output queue set." % (self.__class__.__name__))
            return
        if "UDP" in self.config:
            print "%s" % self.config
            udpListener = UPDListener(self.output_queues)
            udpListener.setDatagramHandler(self.receivers)
            self.registerUDPListener(udpListener)
        if "TCP" in self.config:
            syslogTCP = handlerFactory()
            syslogTCP.setOutputQueues(self.output_queues)
            self.registerTCPListener(syslogTCP)
        self.startRegisterdListeners()