# -*- coding: utf-8 -*-
import sys
import BaseThreadedModule
import BaseModule
from Decorators import ModuleDocstringParser

try:
    import regex as re
except ImportError:
    import re

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

    module_type = "parser"
    """Set module type"""

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

    def handleEvent(self, event):
        """
        This method expects a syslog datagram.
        It might contain more then one event. We split at the newline char.
        """
        # Remove possible remaining syslog error code
        # i.e. event starts with <141>
        fieldname = self.getConfigurationValue('source_field', event)
        if fieldname not in event:
            yield event
            return
        try:
            if event[fieldname].index(">") <= 4:
                event[fieldname] = event[fieldname][event[fieldname].index(">")+1:] + "\n"
        except:
            pass
        yield self.parseEvent(event, fieldname)
        #self.sendEvent(self.parseEvent(event, fieldname))

    def parseEvent(self, event, fieldname):
        """
        When an event type was successfully detected, extract the fields with to corresponding regex pattern.
        """
        string_to_match = event[fieldname]
        matches_dict = False
        for event_type, regex_data in self.fieldextraction_regexpressions.iteritems():
            matches_dict = {}
            if regex_data['match_type'] == 'search':
                matches = regex_data['pattern'].search(string_to_match);
                if matches:
                    matches_dict = matches.groupdict()
            elif regex_data['match_type'] == 'findall':
                for match in regex_data['pattern'].finditer(string_to_match):
                    for key, value in match.groupdict().iteritems():
                        try:
                            matches_dict[key].append(value)
                        except:
                            matches_dict[key] = [value]
            if matches_dict:
                event.update(matches_dict)
                event.update({self.target_field: event_type})
                if(self.break_on_match):
                    break
        if not matches_dict:
            event.update({self.target_field: self.mark_unmatched_as})
        return event