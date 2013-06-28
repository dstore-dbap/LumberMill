import sys
import re
import BaseModule
import lib.StatisticCollector as StatisticCollector

class ClassifiedSyslogMessageParser(BaseModule.BaseModule):
    
    message_types = []
    fieldextraction_regexpressions = {}
    
    def configure(self, configuration):
        for message_type, regex_pattern in configuration['field_extraction_patterns'].items():
            self.message_types.append(message_type)
            try:
                regex = re.compile(regex_pattern)
            except Exception, e:
                self.logger.error("RegEx error for pattern %s. Exception: %s, Error: %s" % (regex_pattern, Exception, e))
                sys.exit(255)
            self.fieldextraction_regexpressions[message_type] = regex

    def handleData(self, message_data):
        try:
            fieldextraction_regexpression = self.fieldextraction_regexpressions[message_data['message_type']]
        except Exception, e:
            self.logger.warn("No regex for message type %s defined. %s, %s" % (message_data['message_type'], Exception, e))
            return        
        self.parseMessage(message_data, fieldextraction_regexpression)
        
    def parseMessage(self,message_data, fieldextraction_regexpression):
        """
        When a message type was successfully detected, extract the fields with to corresponding regex pattern
        """
        self.logger.debug("Input to parseMessage %s" % message_data)
        message_type = message_data['message_type']
        message = message_data['data']
        extracted_fields = {}
        matched = False
        for m in fieldextraction_regexpression.finditer(message):
            matched = True
            message_data.update(m.groupdict())
            try:
                StatisticCollector.StatisticCollector().getDict("parseMessage")[message_type]['hits'] += 1
            except:
                StatisticCollector.StatisticCollector().getDict("parseMessage")[message_type] = {'misses': 0, 'hits': 1}
        
        if not matched:
            self.logger.debug("Could not extract fields for source type %s." % message_type);
            self.logger.debug("Raw message: %s" % message);
            try:
                StatisticCollector.StatisticCollector().getDict("parseMessage")[message_type]['misses'] += 1
            except:
                StatisticCollector.StatisticCollector().getDict("parseMessage")[message_type] = {'misses': 1, 'hits': 0}

        self.logger.debug("Output from parseMessage %s" % message_data)
        try:
            [queue.put(message_data) for queue in self.output_queues]
        except Exception, e:
            self.logger.error("Could not add received data to output queue. Excpeption: %s, Error: %s." % (Exception, e))