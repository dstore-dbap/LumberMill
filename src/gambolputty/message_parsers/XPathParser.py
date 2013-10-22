from lxml import etree
import BaseModule

class XPathParser(BaseModule.BaseModule):
    """Parse an xml string via xpath.
    Configuration example:

    - module: XPathParser
      configuration:
        source-field: 'xml_data'
        query:  '//Item[@%(server_name)s]/@NodeDescription'
    """

    def setup(self):
        """
        Setup method to set default values.
        This method will be called by the GambolPutty main class after initializing the module
        and before the configure method of the module is called.
        """
        # Call parent setup method
        super(XPathParser, self).setup()


    def configure(self, configuration):
        """
        Configure the module.
        This method will be called by the GambolPutty main class after initializing the module
        and after the configure method of the module is called.
        The configuration parameter contains k:v pairs of the yaml configuration for this module.

        @param configuration: dictionary
        @return:
        """
        # Call parent configure method
        super(XPathParser, self).configure(configuration)


    def handleData(self, data):
        """
        Process the event.

        @param data: dictionary
        @return data: dictionary
        """
        for source_field in self.getConfigurationValue('source-fields', data):
            if source_field not in data:
                continue
            xml_string = data[source_field].decode('utf8').encode('ascii', 'ignore')
            xml_root = etree.fromstring(xml_string)
            xml_tree = etree.ElementTree(xml_root)
            print self.getConfigurationValue('query', data)
            result =  xml_tree.xpath(self.getConfigurationValue('query', data))
            if not result:
                continue
            target_field_name = self.getConfigurationValue('target-field', data) if 'target-field' in self.configuration_data else "gambolputty_xpath"
            data[target_field_name] = result
        return data