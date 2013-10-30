# -*- coding: utf-8 -*-
import sys
import re
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class RegexParser(BaseThreadedModule.BaseThreadedModule):
    """
    Parse a string by named regular expressions.

    Configuration example:

    - module: RegexParser
      configuration:
        source-field: field1                    # <default: 'data'; type: string; is: optional>
        mark-on-success: True                   # <default: False; type: boolean; is: optional>
        mark-on-failure: True                   # <default: False; type: boolean; is: optional>
        break-on-match: True                    # <default: True; type: boolean; is: optional>
        field-extraction-patterns:              # <type: dict; is: required>
          httpd_access_log: ['(?P<httpd_access_log>.*)', 're.MULTILINE | re.DOTALL', 'findall']
    """

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        # Set defaults
        supported_regex_match_types = ['search', 'findall']
        self.add_success_marker = True if 'mark-on-success' in configuration else False
        self.add_failure_marker = True if 'mark-on-failure' in configuration else False
        self.break_on_match = configuration['break-on-match'] if 'break-on-match' in configuration else True
        self.message_types = []
        self.fieldextraction_regexpressions = {}
        for message_type, regex_pattern in configuration['field-extraction-patterns'].items():
            regex_options = 0
            regex_match_type = 'search'
            if isinstance(regex_pattern, list):
                i = iter(regex_pattern)
                # Pattern is the first entry
                regex_pattern = i.next()
                # Regex options the second
                try:
                    regex_options = eval(i.next())
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("RegEx error for options %s. Exception: %s, Error: %s" % (regex_options, etype, evalue))
                    self.gp.shutDown()
                # Regex match type the third (optional)
                try:
                    regex_match_type = i.next()
                except:
                    pass
            # Make sure regex_match_type is valid
            # At the moment only search and findall are supported
            if regex_match_type not in supported_regex_match_types:
                self.logger.error("RegEx error for match type %s. Only %s are supported." % (regex_options, supported_regex_match_types))
                self.gp.shutDown()
            try:
                regex = re.compile(regex_pattern, regex_options)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("RegEx error for pattern %s. Exception: %s, Error: %s" % (regex_pattern, etype, evalue))
                self.gp.shutDown()
            self.fieldextraction_regexpressions[message_type] = {'pattern': regex, 'match_type': regex_match_type}

    def handleData(self, data):
        """
        This method expects a syslog datagram.
        It might contain more then one message. We split at the newline char.
        """
        self.logger.debug("Received raw message: %s" % data)
        # Remove possible remaining syslog error code
        # i.e. message starts with <141>
        fieldname = self.getConfigurationValue('source-field', data)
        if fieldname not in data:
            return data
        try:
            if data[fieldname].index(">") <= 4:
                data[fieldname] = data[fieldname][data[fieldname].index(">")+1:] + "\n"
        except:
            pass
        data = self.parseMessage(data, fieldname)
        return data
        
    def parseMessage(self, data, fieldname):
        """
        When a message type was successfully detected, extract the fields with to corresponding regex pattern
        """
        message = data[fieldname]
        matches_dict = False
        self.logger.debug("Input to parseMessage: %s" % message)
        for message_type, regex_data in self.fieldextraction_regexpressions.iteritems():
            matches_dict = {}
            if regex_data['match_type'] == 'search':
                matches = regex_data['pattern'].search(message);
                if matches:
                    matches_dict = matches.groupdict()
            elif regex_data['match_type'] == 'findall':
                for match in regex_data['pattern'].finditer(message):
                    for key, value in match.groupdict().iteritems():
                        try:
                            matches_dict[key].append(value)
                        except:
                            matches_dict[key] = [value]
            if matches_dict:
                data.update(matches_dict)
                data.update({'message_type': message_type})
                if self.add_success_marker:
                    data['markers'].append(self.getConfigurationValue('mark-on-success', data))
                if(self.break_on_match):
                    break
        if not matches_dict:
            if self.add_failure_marker:
                data['markers'].append(self.getConfigurationValue('mark-on-failure', data))
            self.logger.debug("Could not extract fields for message %s." % message);
            data.update({'message_type': 'unknown'})
        self.logger.debug("Output from parseMessage %s" % data)
        return data