# -*- coding: utf-8 -*-
import os
import sys

from pyzabbix import ZabbixMetric, ZabbixSender
from BaseThreadedModule import BaseThreadedModule
from utils.Buffers import Buffer
from utils.Decorators import ModuleDocstringParser
from utils.DynamicValues import mapDynamicValue


@ModuleDocstringParser
class Zabbix(BaseThreadedModule):
    """
    Send events to zabbix.

    hostname: Hostname for which the metrics should be stored.
    fields: Event fields to send.
    field_prefix: Prefix to prepend to field names. For e.g. cpu_count field with default  prefix, the Zabbix key is lumbermill_cpu_count.
    timestamp_field: Field to provide timestamp. If not provided, current timestamp is used.
    agent_conf: Path to zabbix_agent configuration file. If set to True defaults to /etc/zabbix/zabbix_agentd.conf.
    server: Address of zabbix server. If port differs from default it can be set by appending it, e.g. 127.0.0.1:10052.
    store_interval_in_secs: sending data to es in x seconds intervals.
    batch_size: sending data to es if event count is above, even if store_interval_in_secs is not reached.
    backlog_size: maximum count of events waiting for transmission. Events above count will be dropped.

    Configuration template:

    - output.Zabbix:
       hostname:                        # <type: string; is: required>
       fields:                          # <type: list; is: required>
       field_prefix:                    # <default: "lumbermill_"; type: string; is: optional>
       timestamp_field:                 # <default: "timestamp"; type: string; is: optional>
       agent_conf:                      # <default: True; type: boolean||string; is: optional>
       server:                          # <default: False; type: boolean||string; is: required if agent_conf is False else optional>
       store_interval_in_secs:          # <default: 10; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 500; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        BaseThreadedModule.configure(self, configuration)
        self.hostname = self.getConfigurationValue("hostname")
        self.fields = self.getConfigurationValue("fields")
        self.field_prefix = self.getConfigurationValue("field_prefix")
        self.timestamp_field = self.getConfigurationValue("timestamp_field")
        self.batch_size = self.getConfigurationValue('batch_size')
        self.backlog_size = self.getConfigurationValue('backlog_size')
        self.agent_conf = self.getConfigurationValue("agent_conf")
        if self.agent_conf:
            if self.agent_conf is True:
                self.agent_conf = "/etc/zabbix/zabbix_agentd.conf"
            if not os.path.isfile(self.agent_conf):
                self.logger.error("%s does not point to an existing file." % self.agent_conf)
                self.lumbermill.shutDown()
            self.zabbix_sender = ZabbixSender(use_config=self.agent_conf)

        else:
            self.logger.error("asdads")
            server = self.getConfigurationValue("server")
            port = 10051
            if ":" in self.server:
                server, port = self.server.split(":")
            self.zabbix_sender = ZabbixSender(zabbix_server=server, port=port)
        self.buffer = Buffer(self.getConfigurationValue('batch_size'), self.storeData,
                             self.getConfigurationValue('store_interval_in_secs'),
                             maxsize=self.getConfigurationValue('backlog_size'))

    def getStartMessage(self):
        if self.agent_conf:
            return "Config: %s. Max buffer size: %d" % (self.agent_conf, self.getConfigurationValue('backlog_size'))
        else:
            return "Server: %s. Max buffer size: %d" % (self.getConfigurationValue("server"), self.getConfigurationValue('backlog_size'))

    def initAfterFork(self):
        BaseThreadedModule.initAfterFork(self)
        self.buffer = Buffer(self.getConfigurationValue('batch_size'), self.storeData,
                             self.getConfigurationValue('store_interval_in_secs'),
                             maxsize=self.getConfigurationValue('backlog_size'))

    def handleEvent(self, event):
        self.buffer.append(event)
        yield None

    def storeData(self, events):
        packet = []
        for event in events:
            if self.timestamp_field:
                try:
                    timestamp = event[self.timestamp_field]
                except KeyError:
                    timestamp = None
            hostname = mapDynamicValue(self.hostname, mapping_dict=event, use_strftime=True)
            for field_name in self.fields:
                try:
                    packet.append(ZabbixMetric(hostname, "%s%s" % (self.field_prefix, field_name), event[field_name], timestamp))
                except KeyError:
                    pass
                    #self.logger.warning("Could not send metrics for %s:%s. Field not found." % (hostname, field_name))
        response = self.zabbix_sender.send(packet)
        if response.failed != 0:
            self.logger.warning("%d of %d metrics were not processed correctly." % (response.total-response.processed, response.total))

    def shutDown(self):
        self.buffer.flush()
