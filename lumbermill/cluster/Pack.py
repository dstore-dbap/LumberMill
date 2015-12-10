# -*- coding: utf-8 -*-
import os
import re
import sys
import socket
import time
import collections
import hashlib
import threading
import msgpack
from Crypto import Random
from Crypto.Cipher import AES

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser, setInterval


class PackMember:

    def __init__(self, host, hostname=None):
        self.host = host
        self.ip_address = host[0]
        self.port = host[1]
        self.hostname = hostname
        self.last_seen = time.time()

    def getHost(self):
        return self.host

    def getIp(self):
        return self.ip_address

    def getPort(self):
        return self.port

    def getHostName(self):
        if not self.hostname:
            try:
                self.hostname = socket.gethostbyaddr(self.ip_address)
            except:
                self.hostname = self.ip_address
        return self.hostname

    def updateLastSeen(self):
        self.last_seen = time.time()

    def isAlive(self):
        return True if time.time() - self.last_seen < 30 else False



@ModuleDocstringParser
class Pack(BaseThreadedModule):
    """
    Pack base module. Handles pack leader discovery and alive checks of pack followers.

    IMPORTANT:
    This is just a first alpha implementation. No leader election, no failover, no sanity checks for conflicting leaders.

    name: Name of the cluster. Used for auto-discovery in same network.
    secret: pre shared key to en/decrypt cluster messages.
    broadcast: Ipaddress for udp broadcasts.
    interface:  Ipaddress to listen on.
    port:   Port to listen on.
    interval: Autodiscover interval.
    pack: Set this node to be either leader or member.

    Configuration template:

    - Pack:
       name:                            # <type: string; is: required>
       secret:                          # <type: string; is: required>
       broadcast:                       # <type: string; is: required>
       interface:                       # <default: '0.0.0.0'; type: string; is: optional>
       port:                            # <default: 5252; type: integer; is: optional>
       interval:                        # <default: 10; type: integer; is: optional>
       pack:                            # <default: 'leader'; type: string; values: ['leader', 'follower']; is: optional>
    """

    module_type = "stand_alone"
    """ Set module type. """

    can_run_forked = False

    def configure(self, configuration):
        import logging
        # self.logger.setLevel(logging.DEBUG)
        # Call parent configure method.
        BaseThreadedModule.configure(self, configuration)
        self.is_leader = True if self.getConfigurationValue('pack') == 'leader' else False
        self.pack_followers = {}
        self.cluster_name = self.getConfigurationValue('name')
        self.discovered_leader = None
        self.secret = hashlib.sha256(self.getConfigurationValue('secret')).digest()
        self.handlers = collections.defaultdict(list)
        self.lock = threading.Lock()
        # Setup socket.
        self.interface_addr = self.getConfigurationValue('interface')
        self.interface_port = self.getConfigurationValue('port')
        self.broadcast_addr = self.getConfigurationValue('broadcast')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.settimeout(1)
        self.hostname = socket.gethostname()
        try:
            self.socket.bind((self.interface_addr, self.interface_port))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not listen on %s:%s. Exception: %s, Error: %s." % (self.getConfigurationValue("interface"),
                                                                                        self.getConfigurationValue("port"), etype, evalue))
            self.alive = False
            self.lumbermill.shutDown()
            return
        self.addHandlers()

    def addHandlers(self):
        handle_marker = 'leaderHandle' if self.is_leader else 'followerHandle'
        for method_name in dir(self):
            if not method_name.startswith(handle_marker):
                continue
            action_name = method_name.replace(handle_marker, '')
            action_name = self.convertCamelCaseToUnderScore(action_name)
            self.addHandler(action_name, getattr(self, method_name))

    def convertCamelCaseToUnderScore(self, camel_case):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_case)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def encrypt(self, message):
        x = AES.block_size - len(message) % AES.block_size
        message = message + (chr(x) * x)
        iv = Random.OSRNG.posix.new().read(AES.block_size)
        cipher = AES.new(self.secret, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(message)

    def decrypt(self, message):
        unpad = lambda s: s[:-ord(s[-1])]
        iv = message[:AES.block_size]
        cipher = AES.new(self.secret, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(message))[AES.block_size:]

    def getDefaultMessageDict(self, action, custom_dict={}):
        message_dict = {'action': action, 'sender': self.hostname, 'cluster': self.cluster_name, 'timestamp': time.time()}
        message_dict.update(custom_dict)
        return message_dict

    def getPackMembers(self):
        return self.pack_followers

    def getDiscoveredLeader(self):
        return self.discovered_leader

    def sendBroadcastMessage(self, message):
         # msgpack encode end encrypt message.
        str_msg = msgpack.packb(message)
        str_msg = self.encrypt(str_msg)
        try:
            self.socket.sendto(str_msg, (self.broadcast_addr, self.interface_port))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not send broadcast message %s to %s. Exception: %s, Error: %s." % (message, host, etype, evalue))

    def sendMessage(self, message, ip_address):
        self.logger.debug("Sending message %s to %s." % (message, ip_address))
         # Json encode end encrypt message.
        str_msg = msgpack.packb(message)
        str_msg = self.encrypt(str_msg)
        try:
            self.socket.sendto(str_msg, (ip_address, self.interface_port))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not send message %s to %s. Exception: %s, Error: %s." % (message, ip_address, etype, evalue))

    def sendMessageToPackFollower(self, pack_member, message):
        if pack_member not in self.pack_followers.values():
            self.logger.warning('Can not send message to unknown pack follower %s.' % pack_member)
            return
        self.sendMessage(message, pack_member.getIp())

    def sendMessageToPack(self, message):
        for pack_member in self.pack_followers.itervalues():
            self.sendMessageToPackFollower(pack_member, message)

    def sendMessageToPackLeader(self, message):
        self.sendMessage(message, self.discovered_leader.getIp())


    def addHandler(self, action, callback):
        self.logger.debug('Adding handler %s for %s.' % (callback, action))
        self.handlers[action].append(callback)

    def run(self):
        if self.is_leader:
            Utils.TimedFunctionManager.startTimedFunction(self.sendAliveRequests)
            Utils.TimedFunctionManager.startTimedFunction(self.sendDiscoverBroadcast)
            Utils.TimedFunctionManager.startTimedFunction(self.dropDeadPackFollowers)
        else:
            Utils.TimedFunctionManager.startTimedFunction(self.dropDeadPackLeader)
        self.logger.info("Running as pack %s." % self.getConfigurationValue('pack'))
        while self.alive:
            try:
                message, host = self.socket.recvfrom(64536)
            except socket.timeout:
                continue
            try:
                # Decrypt and msgpack decode message.
                message = msgpack.unpackb(self.decrypt(message))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Could not parse cluster message %s. Maybe your secrets differ? Exception: %s, Error: %s." % (message, etype, evalue))
                continue
            # Ignore messages for other clusters and from self.
            if message['cluster'] != self.cluster_name or message['sender'] == self.hostname:
                continue
            self.logger.info("Received message %s from %s." % (message, host[0]))
            if message['action'] not in self.handlers.keys():
                self.logger.warning('Got request for unknown handler %s.' % message['action'])
            # Excecute callbacks
            for callback in self.handlers["%s" % message['action']]:
                self.logger.debug('Calling callback %s for %s.' % (callback, message['action']))
                callback(host, message)

    @setInterval(10, call_on_init=True)
    def sendDiscoverBroadcast(self):
        """
        Leader sends udp broadcast messages every 10 seconds.
        """
        message = self.getDefaultMessageDict(action='discovery_request')
        self.logger.debug('Sending broadcast pack follower discovery.')
        self.sendBroadcastMessage(message)

    @setInterval(10)
    def sendAliveRequests(self):
        """
        Leader sends alive requests to all dicovered followers every 10 seconds.
        """
        for ip_address, pack_follower in self.pack_followers.items():
            message = self.getDefaultMessageDict(action='alive_request')
            self.sendMessageToPackFollower(pack_follower, message)

    @setInterval(10)
    def dropDeadPackFollowers(self):
        """
        Drop followers who have not been seen the last 30 seconds.
        @see PackMember.isAlive() and PackMember.updateLastSeen()
        """
        with self.lock:
            for ip_address, pack_follower in self.pack_followers.items():
                if pack_follower.isAlive():
                    continue
                self.logger.warning('Dropping dead pack follower %s, %s.' % (pack_follower.getHostName(), ip_address))
                self.pack_followers.pop(ip_address)

    @setInterval(1)
    def dropDeadPackLeader(self):
        """
        Drop leader who has not been seen the last 30 seconds.
        @see PackMember.isAlive() and PackMember.updateLastSeen()
        """
        if not self.discovered_leader:
            return
        with self.lock:
            if self.discovered_leader.isAlive():
                return
            self.logger.warning('Dropping dead pack leader %s, %s.' % (self.discovered_leader.getHostName(), self.discovered_leader.getIp()))
            self.discovered_leader = None

    """
    Pack follower discovery procedure.

    - leader sends a broadcast 'discovery_request' message
    - follower replies with a 'discovery_reply' message
    - leader replies with a 'discovery_finish' message
    - follower sets its discovered leader
    """
    def followerHandleDiscoveryRequest(self, sender, message):
        sender_ip = sender[0]
        if self.discovered_leader and self.discovered_leader.getIp() == sender_ip:
            return
        message = self.getDefaultMessageDict(action='discovery_reply')
        self.sendMessage(message, sender[0])

    def leaderHandleDiscoveryReply(self, sender, message):
        self.logger.info("Discovered %s as pack member in pid %s." % (message['sender'], os.getpid()))
        sender_ip = sender[0]
        try:
            pack_member = self.pack_followers[sender_ip]
        except KeyError:
            pack_member = PackMember(sender, message['sender'])
            self.pack_followers[sender_ip] = pack_member
        message = self.getDefaultMessageDict(action='discovery_finish')
        self.sendMessage(message, pack_member.getIp())

    def followerHandleDiscoveryFinish(self, sender, message):
        self.logger.info("Discovered %s as pack leader." % message['sender'])
        self.discovered_leader = PackMember(sender, message['sender'])

    """
    Pack follower alive procedure.

    - leader sends an 'alive_request' message
    - follower replies with a 'alive_reply' message
    - leader calls follower.updateLastSeen() and replies with a 'alive_finish' message
    - follower calls leader.updateLastSeen()
    """
    def followerHandleAliveRequest(self, sender, message):
        sender_ip = sender[0]
        if not self.discovered_leader or sender_ip != self.discovered_leader.getIp():
            return
        self.logger.debug('Got alive request from %s.' % sender_ip)
        message = self.getDefaultMessageDict(action='alive_reply')
        self.sendMessageToPackLeader(message)

    def leaderHandleAliveReply(self, sender, message):
        try:
            pack_follower = self.pack_followers[sender[0]]
        except KeyError:
            return
        self.logger.debug('Got alive reply from %s.' % pack_follower.getHostName())
        with self.lock:
            pack_follower.updateLastSeen()
        message = self.getDefaultMessageDict(action='alive_finish')
        self.sendMessageToPackFollower(pack_follower, message)

    def followerHandleAliveFinish(self, sender, message):
        sender_ip = sender[0]
        if not self.discovered_leader or sender_ip != self.discovered_leader.getIp():
            return
        self.discovered_leader.updateLastSeen()

    def shutDown(self):
        # Call parent configure method.
        BaseThreadedModule.shutDown(self)
        self.socket.close()
        self.socket = None

