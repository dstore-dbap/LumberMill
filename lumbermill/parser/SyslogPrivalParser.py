# -*- coding: utf-8 -*-
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class SyslogPrivalParser(BaseThreadedModule):
    """
    It will parse the source field in the event dictionary for the default severity
    and facility fields (RFC5424, http://tools.ietf.org/html/rfc5424).
    The source field must contain the prival with the pattern: "\d+"

    Numerical             Facility
     Code

      0             kernel messages
      1             user-level messages
      2             mail system
      3             system daemons
      4             security/authorization messages
      5             messages generated internally by syslogd
      6             line printer subsystem
      7             network news subsystem
      8             UUCP subsystem
      9             clock daemon
     10             security/authorization messages
     11             FTP daemon
     12             NTP subsystem
     13             log audit
     14             log alert
     15             clock daemon (note 2)
     16             local use 0  (local0)
     17             local use 1  (local1)
     18             local use 2  (local2)
     19             local use 3  (local3)
     20             local use 4  (local4)
     21             local use 5  (local5)
     22             local use 6  (local6)
     23             local use 7  (local7)

    Numerical         Severity
     Code

      0       Emergency: system is unusable
      1       Alert: action must be taken immediately
      2       Critical: critical conditions
      3       Error: error conditions
      4       Warning: warning conditions
      5       Notice: normal but significant condition
      6       Informational: informational messages
      7       Debug: debug-level messages

    Configuration template:

    - SyslogPrivalParser:
       source_field:                    # <default: 'syslog_prival'; type: string; is: optional>
       map_values: False                # <default: True; type: boolean; is: optional>
       facility_mappings:               # <default: {}; type: dictionary; is: optional>
       severity_mappings:               # <default: {}; type: dictionary; is: optional>
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""

    rfc_5424_facilities = { 0:  "kernel messages",
                          1: "user-level",
                          2: "mail",
                          3: "system",
                          4: "security/authorization",
                          5: "syslogd",
                          6: "line printer",
                          7: "network news",
                          8: "UUCP",
                          9: "clock",
                         10: "security/authorization",
                         11: "FTP",
                         12: "NTP",
                         13: "log audit",
                         14: "log alert",
                         15: "clock",
                         16: "local0",
                         17: "local1",
                         18: "local2",
                         19: "local3",
                         20: "local4",
                         21: "local5",
                         22: "local6",
                         23: "local7"}

    rfc_5424_severities = { 0: "Emergency",
                          1: "Alert",
                          2: "Critical",
                          3: "Error",
                          4: "Warning",
                          5: "Notice",
                          6: "Informational",
                          7: "Debug"}

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')
        self.facility_mappings = dict(self.rfc_5424_facilities.items() + self.getConfigurationValue('facility_mappings').items())
        self.severity_mappings = dict(self.rfc_5424_severities.items() + self.getConfigurationValue('severity_mappings').items())

    def handleEvent(self, event):
        try:
            prival = int(event[self.source_field])
        except:
            yield event
            return
        # Calculate facility and priority from PRIVAL (@see: http://tools.ietf.org/html/rfc5424#section-6.2.1)
        event['syslog_facility'] = prival >> 3
        event['syslog_severity'] = prival & 7
        if not self.getConfigurationValue('map_values'):
            yield event
            return
        try:
            event['syslog_facility'] = self.facility_mappings[event['syslog_facility']]
            event['syslog_severity'] = self.severity_mappings[event['syslog_severity']]
        except KeyError:
            pass
        yield event
