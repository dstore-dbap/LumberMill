# -*- coding: utf-8 -*-
import logging
import sys
import socket
import time
import collections
import BaseThreadedModule
import Utils
import Decorators
import hashlib
from Crypto import Random
from Crypto.Cipher import AES

json = False
for module_name in ['yajl', 'simplejson', 'json']:
    try:
        json = __import__(module_name)
        break
    except ImportError:
        pass
if not json:
    raise ImportError

@Decorators.ModuleDocstringParser
class Cluster(BaseThreadedModule.BaseThreadedModule):
    """
    Container module for all cluster related plugins.

    IMPORTANT:
    This is just a first alpha implementation. No leader election, no failover, no sanity checks for conflicting leaders.

    interface:  Ipaddress to listen on.
    port:   Port to listen on.
    broadcast: Ipaddress for udp broadcasts.
    interval: Autodiscover interval.
    tornado_webserver: Name of the webserver module. Needed for leader - pack communication.
    pack: Set this node to be either leader or member.
    name: Name of the cluster. Used for auto-discovery in same network.
    shared_secret: pre shared key to en/decrypt cluster messages.

    Module dependencies: WebserverTornado

    Configuration example:

    - module: Cluster
      interface:                            # <default: '0.0.0.0'; type: string; is: optional>
      port:                                 # <default: 5252; type: integer; is: optional>
      broadcast:                            # <type: string; is: required>
      interval:                             # <default: 10; type: integer; is: optional>
      pack:                                 # <default: 'leader'; type: string; values: ['leader', 'member']; is: optional>
      name:                                 # <type: string; is: required>
      secret:                               # <type: string; is: required>
    """

    module_type = "stand_alone"
    """ Set module type. """

    can_run_parallel = False

    def configure(self, configuration):
        # Call parent configure method.
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        #self.logger.setLevel(logging.DEBUG)
        self.leader = True if self.getConfigurationValue('pack') == 'leader' else False
        self.pack_members = []
        self.dying_pack_members = []
        self.pending_alive_resonses = {}
        self.cluster_name = self.getConfigurationValue('name')
        self.discovered_leader = None
        self.secret = hashlib.sha256(self.getConfigurationValue('secret')).digest()
        self.handlers = collections.defaultdict(list)
        # Setup socket.
        self.interface_addr = self.getConfigurationValue('interface')
        self.interface_port = self.getConfigurationValue('port')
        self.broadcast_addr = self.getConfigurationValue('broadcast')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.hostname = socket.gethostname()
        # Add handlers.
        self.addHandler('discovery_call', self.handleDiscoveryCall)
        self.addHandler('discovery_reply', self.handleDiscoveryReply)
        self.addHandler('discovery_finish', self.handleDiscoveryFinish)
        self.addHandler('alive_call', self.handleAliveCall)
        self.addHandler('alive_reply', self.handleAliveReply)

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
        message_dict = {'action': action, 'sender': self.hostname, 'cluster': self.cluster_name, 'leader': self.leader, 'timestamp': time.time()}
        message_dict.update(custom_dict)
        return message_dict

    def sendMessage(self, message, host):
         # Json encode end encrypt message.
        message = self.encrypt(json.dumps(message))
        self.socket.sendto(message, host)

    def sendMessageToPackMember(self, message, pack_member):
        self.logger.debug("%sSending message %s to %s.%s" % (Utils.AnsiColors.OKBLUE, message, pack_member, Utils.AnsiColors.ENDC))
        if pack_member not in self.pack_members:
            self.logger.warning('%sCan not send message to unknown pack member %s.%s' % (Utils.AnsiColors.WARNING, pack_member,Utils.AnsiColors.ENDC))
            return
        self.sendMessage(message, pack_member)

    def sendMessageToPack(self, message):
        for pack_member in self.pack_members:
            self.sendMessageToPackMember(message, pack_member)

    def run(self):
        try:
            self.socket.bind((self.interface_addr, self.interface_port))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not listen on %s:%s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue("interface"),
                                                                                       self.getConfigurationValue("port"), etype, evalue, Utils.AnsiColors.ENDC))
            self.gp.shutDown()
            return
        # Start alive requests only if we are the leader.
        if self.leader:
            self.startTimedFunction(self.sendAliveRequests)
        # Start discovery of master server if we are a simple pack member.
        if not self.leader:
            self.startTimedFunction(self.sendDiscoverBroadcast)
        while self.is_alive:
            message, host = self.socket.recvfrom(16384)
            try:
                # Decrypt and json decode message.
                message = json.loads(self.decrypt(message))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("%sCould not parse cluster message %s. Maybe your secrets differ? Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, message, etype, evalue, Utils.AnsiColors.ENDC))
                continue
            # Ignore messages from self and messages to other clusters.
            if message['sender'] == self.hostname or message['cluster'] != self.cluster_name:
                continue
            self.logger.debug("%sReceived action %s.%s" % (Utils.AnsiColors.OKBLUE, message['action'], Utils.AnsiColors.ENDC))
            # Excecute callbacks
            for callback in self.handlers["%s" % message['action']]:
                self.logger.debug('%sCalling callback %s for %s.%s' % (Utils.AnsiColors.OKBLUE, callback, message['action'], Utils.AnsiColors.ENDC))
                callback(message, host)

    def getPackMembers(self):
        return self.pack_members

    def addHandler(self, action, callback):
        self.logger.debug('%sAdding handler %s for %s.%s' % (Utils.AnsiColors.OKBLUE, callback, action, Utils.AnsiColors.ENDC))
        self.handlers[action].append(callback)

    @Decorators.setInterval(60, call_on_init=True)
    def sendDiscoverBroadcast(self):
        message = self.getDefaultMessageDict(action='discovery_call')
        self.logger.debug('%sSending broadcast pack discovery.%s' % (Utils.AnsiColors.OKBLUE, Utils.AnsiColors.ENDC))
        self.sendMessage(message, (self.broadcast_addr, self.interface_port))

    @Decorators.setInterval(10)
    def sendAliveRequests(self):
        drop_dead_pack_member_timed_func = self.getDropDeadPackMemberTimedFunc()
        for pack_member in self.pack_members:
            message = self.getDefaultMessageDict(action='alive_call')
            self.sendMessageToPackMember(message, pack_member)
            self.dying_pack_members.append(pack_member)
            self.pending_alive_resonses.update({pack_member: self.startTimedFunction(drop_dead_pack_member_timed_func, pack_member)})

    def getDropDeadPackMemberTimedFunc(self):
        @Decorators.setInterval(5, max_run_count=1)
        def dropDeadPackMembers(dying_pack_member):
            try:
                self.dying_pack_members.remove(dying_pack_member)
                self.pack_members.remove(dying_pack_member)
                self.logger.warning('%sDropping dead pack member %s.%s' % (Utils.AnsiColors.WARNING, dying_pack_member, Utils.AnsiColors.ENDC))
            except ValueError:
                self.logger.info("asdasd")
        return dropDeadPackMembers

    ####
    # Pack member discovery.
    ####
    def handleDiscoveryCall(self, message, host):
        # Only send reply to discover call if we are a pack leader.
        if not self.leader:
            return
        message = self.getDefaultMessageDict(action='discovery_reply')
        self.sendMessage(message, host)

    def handleDiscoveryReply(self, message, host):
        # Only pack members should handle discover replies.
        if self.leader:
            return
        message = self.getDefaultMessageDict(action='discovery_finish', custom_dict={'success': True})
        self.sendMessage(message, host)
        if self.discovered_leader != host:
            self.logger.info("%sDiscovered %s as pack leader.%s" % (Utils.AnsiColors.LIGHTBLUE, host, Utils.AnsiColors.ENDC))
            self.discovered_leader = host

    def handleDiscoveryFinish(self, message, host):
        # Only send reply to discover finish call if we are a pack leader.
        if not self.leader:
            return
        if message['success'] and host not in self.pack_members:
            self.logger.info("%sDiscovered %s as pack member.%s" % (Utils.AnsiColors.LIGHTBLUE, host, Utils.AnsiColors.ENDC))
            self.pack_members.append(host)

    ####
    # Pack member alive check.
    ####
    def handleAliveCall(self, message, host):
        # Only send reply to alive call if we are a pack member.
        if self.leader:
            return
        self.logger.debug('%sGot alive request from %s.%s' % (Utils.AnsiColors.OKBLUE, host, Utils.AnsiColors.ENDC))
        message = self.getDefaultMessageDict(action='alive_reply', custom_dict={'reply': 'I am not dead!'})
        self.sendMessage(message, host)

    def handleAliveReply(self, message, host):
        # Only leader may handle alive replies.
        if not self.leader:
            return
        try:
            if message['reply'] == 'I am not dead!':
                # Stop timed function to remove pending host from pack members.
                self.stopTimedFunctions(self.pending_alive_resonses[host])
        except ValueError:
            self.logger.info("asdasd")
            pass

    def shutDown(self):
        # Call parent configure method.
        BaseThreadedModule.BaseThreadedModule.shutDown(self)
        self.socket.close()
        self.socket = None