import sys
import re
import BaseModule

class SyslogMessageClassifier(BaseModule.BaseModule):
    
    classification_regexpressions = {}
    message_types = []
 
    def configure(self, configuration):
        for message_type, regex_pattern in configuration['classification_patterns'].items():
            self.message_types.append(message_type)
            try:
                regex = re.compile(regex_pattern)
            except Exception, e:
                self.logger.error("RegEx error for pattern %s. Exception: %s, Error: %s" % (regex_pattern, Exception, e))
                sys.exit(255)
            self.classification_regexpressions[message_type] = regex
 
    def handleData(self, data):
        """
        This method expects a syslog datagram.
        It might contain more then one message. We split at the newline char.

        Use a regex pattern to detect the message type.
        The list of regex patterns will be resorted according to 
        the number of matches they produced. This way "hot" patterns
        will be tested first.

        """
        self.logger.debug("Received raw message: %s" % data)
        source_ip = data['received_from']
        syslog_messages = data['data']
        messages = syslog_messages.split("\n");
        for message in messages:
            # Remove possible remaining syslog error code
            # i.e. message starts with <141>
            try:
                if message.index(">") <= 4:
                    message = message[message.index(">")+1:] + "\n"
            except: 
                pass
            if message.strip() == "":
                return

            matches = False;
            
            for message_type in self.message_types:
                matches = self.classification_regexpressions[message_type].search(message);
                if matches:
                    break;
                
            if not matches:
                self.logger.debug("Could not classify Message via regexpatterns in classifications.conf");
                self.logger.debug("Classified as unknown.");
                self.logger.debug("Raw message: "+message);
                message_type = 'unknown'
    
            message_data = {'source_ip': source_ip, 'message_type': message_type, 'data': message}
            try:
                [queue.put(message_data) for queue in self.output_queues]
            except Exception, e:
                self.logger.error("Could not add received data to output queue. Excpeption: %s, Error: %s." % (Exception, e))