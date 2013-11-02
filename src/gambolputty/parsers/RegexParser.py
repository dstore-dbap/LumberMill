# -*- coding: utf-8 -*-
import sys
import re
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class RegexParser(BaseThreadedModule.BaseThreadedModule):
    """
    Parse a string by named regular expressions.

    If regex metches, fields in the data dictionary will be set as defined in the named regular expression.
    Additionally the field "event_type" will be set containing the name of the regex.
    In the example below this would be "httpd_access_log".

    Configuration example:

    - module: RegexParser
      configuration:
        source_field: field1                    # <default: 'data'; type: string; is: optional>
        mark_unmatched_as: unknown              # <default: 'unknown'; type: string; is: optional>
        break_on_match: True                    # <default: True; type: boolean; is: optional>
        field_extraction_patterns:              # <type: dict; is: required>
          httpd_access_log: ['(?P<httpd_access_log>.*)', 're.MULTILINE | re.DOTALL', 'findall']
    """

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        # Set defaults
        supported_regex_match_types = ['search', 'findall']
        self.target_field = "event_type"
        self.mark_unmatched_as = self.getConfigurationValue('mark_unmatched_as')
        self.break_on_match = self.getConfigurationValue('break_on_match')
        self.event_types = []
        self.fieldextraction_regexpressions = {}
        for event_type, regex_pattern in configuration['field_extraction_patterns'].items():
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
            self.fieldextraction_regexpressions[event_type] = {'pattern': regex, 'match_type': regex_match_type}

    def handleData(self, data):
        """
        This method expects a syslog datagram.
        It might contain more then one event. We split at the newline char.
        """
        self.logger.debug("Received raw event: %s" % data)
        # Remove possible remaining syslog error code
        # i.e. event starts with <141>
        fieldname = self.getConfigurationValue('source_field', data)
        if fieldname not in data:
            yield data
        try:
            if data[fieldname].index(">") <= 4:
                data[fieldname] = data[fieldname][data[fieldname].index(">")+1:] + "\n"
        except:
            pass
        data = self.parseEvent(data, fieldname)
        yield data
        
    def parseEvent(self, data, fieldname):
        """
        When an event type was successfully detected, extract the fields with to corresponding regex pattern.
        """
        event = data[fieldname]
        matches_dict = False
        self.logger.debug("Input to parseEvent: %s" % event)
        for event_type, regex_data in self.fieldextraction_regexpressions.iteritems():
            matches_dict = {}
            if regex_data['match_type'] == 'search':
                matches = regex_data['pattern'].search(event);
                if matches:
                    matches_dict = matches.groupdict()
            elif regex_data['match_type'] == 'findall':
                for match in regex_data['pattern'].finditer(event):
                    for key, value in match.groupdict().iteritems():
                        try:
                            matches_dict[key].append(value)
                        except:
                            matches_dict[key] = [value]
            if matches_dict:
                data.update(matches_dict)
                data.update({self.target_field: event_type})
                if(self.break_on_match):
                    break
        if not matches_dict:
            data.update({self.target_field: self.mark_unmatched_as})
        return data