# -*- coding: utf-8 -*-
import sys
import re
import os
from operator import itemgetter

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser, setInterval


@ModuleDocstringParser
class RegexParser(BaseThreadedModule):
    """
    Parse a string by named regular expressions.

    If regex matches, fields in the data dictionary will be set as defined in the named regular expression.
    Additionally the field "lumbermill.event_type" will be set containing the name of the regex.
    In the example below this would be "httpd_access_log".

    It is also possible to define multiple regexes with the same name. This allows for different log patterns
    for the same log type, e.g. apache access logs and nginx access logs.

    source_field: Field to apply the regex to.
    mark_unmatched_as: Set <lumbermill.event_type> to this value if regex did not match.
    break_on_match: Stop applying regex patterns after first match.
    hot_rules_first: Apply regex patterns based on their hit count.

    Configuration template:

    - RegexParser:
       source_field:                    # <default: 'data'; type: string; is: optional>
       mark_unmatched_as:               # <default: 'Unknown'; type: string; is: optional>
       break_on_match:                  # <default: True; type: boolean; is: optional>
       hot_rules_first:                 # <default: True; type: boolean; is: optional>
       field_extraction_patterns:       # <type: list; is: required>
        - httpd_access_log: ['(?P<httpd_access_log>.*)', 're.MULTILINE | re.DOTALL', 'findall']
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        # Set defaults
        supported_regex_match_types = ['search', 'findall']
        self.timed_func_handler = None
        self.source_field = self.getConfigurationValue('source_field')
        self.mark_unmatched_as = self.getConfigurationValue('mark_unmatched_as')
        self.break_on_match = self.getConfigurationValue('break_on_match')
        self.hot_rules_first = self.getConfigurationValue('hot_rules_first')
        self.event_types = []
        self.fieldextraction_regexpressions = []
        self.logstash_patterns = {}
        self.readLogstashPatterns()
        for regex_config in configuration['field_extraction_patterns']:
            event_type = regex_config.keys()[0]
            regex_pattern = regex_config[event_type]
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
                    self.logger.error("RegEx error for options %s. Exception: %s, Error: %s." % (regex_options, etype, evalue))
                    self.lumbermill.shutDown()
                    return
                # Regex match type the third (optional)
                try:
                    regex_match_type = i.next()
                except:
                    pass
            # Make sure regex_match_type is valid
            # At the moment only search and findall are supported
            if regex_match_type not in supported_regex_match_types:
                self.logger.error("RegEx error for match type %s. Only %s are supported." % (regex_options, supported_regex_match_types))
                self.lumbermill.shutDown()
                return
            try:
                regex_pattern = self.replaceLogstashPatterns(regex_pattern)
                regex = re.compile(regex_pattern, regex_options)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("RegEx error for %s pattern %s. Exception: %s, Error: %s." % (event_type, regex_pattern, etype, evalue))
                self.lumbermill.shutDown()
            self.fieldextraction_regexpressions.append({'event_type': event_type, 'pattern': regex, 'match_type': regex_match_type, 'hitcounter': 0})

    def initAfterFork(self):
        if self.hot_rules_first:
            resort_fieldextraction_regexpressions_func = self.getResortFieldextractionRegexpressionsFunc()
            self.timed_func_handler = Utils.TimedFunctionManager.startTimedFunction(resort_fieldextraction_regexpressions_func)
        BaseThreadedModule.initAfterFork(self)

    def getResortFieldextractionRegexpressionsFunc(self):
        @setInterval(10)
        def resortFieldextractionRegexpressions():
            """Resort the regular expression list, according to hitcount. Might speed up matching"""
            self.fieldextraction_regexpressions = sorted(self.fieldextraction_regexpressions, key=itemgetter('hitcounter'), reverse=True)
            for regex_data in self.fieldextraction_regexpressions:
                regex_data['hitcounter'] = 0
        return resortFieldextractionRegexpressions

    def readLogstashPatterns(self):
        path = "%s/../assets/grok_patterns" % os.path.dirname(os.path.realpath(__file__))
        for (dirpath, dirnames, filenames) in os.walk(path):
            for filename in filenames:
                lines = [line.strip() for line in open('%s%s%s' % (dirpath, os.sep, filename))]
                for line_no, line in enumerate(lines):
                    if line == "" or line.startswith('#'):
                        continue
                    try:
                        pattern_name, pattern = line.split(' ', 1)
                        self.logstash_patterns[pattern_name] = pattern
                    except:
                        etype, evalue, etb = sys.exc_info()
                        self.logger.warning("Could not read logstash pattern in file %s%s%s, line %s. Exception: %s, Error: %s." % (dirpath,  os.sep, filename, line_no+1, etype, evalue))

    def replaceLogstashPatterns(self, regex_pattern):
        #print regex_pattern
        pattern_name_re = re.compile('%\{(.*?)\}')
        for match in pattern_name_re.finditer(regex_pattern):
            for pattern_name in match.groups():
                pattern_identifier = False
                if ':' in pattern_name:
                    pattern_name, pattern_identifier = pattern_name.split(':')
                try:
                    logstash_pattern = self.replaceLogstashPatterns(self.logstash_patterns[pattern_name])
                    if not pattern_identifier:
                        regex_pattern = regex_pattern.replace('%%{%s}' % pattern_name, logstash_pattern)
                    else:
                        regex_pattern = regex_pattern.replace('%%{%s:%s}' % (pattern_name, pattern_identifier), '(?P<%s>%s)' % (pattern_identifier, logstash_pattern))
                except KeyError:
                    self.logger.warning("Could not parse logstash pattern %s. Pattern name not found in pattern files." % (pattern_name))
                    continue
        return regex_pattern

    def handleEvent(self, event):
        """
        When an event type was successfully detected, extract the fields with to corresponding regex pattern.
        """
        if self.source_field not in event:
            yield event
            return
        string_to_match = event[self.source_field]
        matches_dict = False
        for regex_data in self.fieldextraction_regexpressions:
            event_type = regex_data['event_type']
            matches_dict = {}
            if regex_data['match_type'] == 'search':
                matches = regex_data['pattern'].search(string_to_match)
                if matches:
                    matches_dict = matches.groupdict()
            elif regex_data['match_type'] == 'findall':
                for match in regex_data['pattern'].finditer(string_to_match):
                    for key, value in match.groupdict().items():
                        try:
                            matches_dict[key].append(value)
                        except:
                            matches_dict[key] = [value]
            if matches_dict:
                event.update(matches_dict)
                event['lumbermill']['event_type'] = event_type
                if self.hot_rules_first:
                    regex_data['hitcounter'] += 1
                if(self.break_on_match):
                    break
        if not matches_dict:
            event['lumbermill']['event_type'] = self.mark_unmatched_as
        yield event