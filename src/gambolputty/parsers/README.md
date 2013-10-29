Parser modules
==========

#####RegexParser

Parse a string by named regular expressions.

Configuration example:

    - module: RegexParser
      configuration:
        source-field: field1                    # <default: 'data'; type: string; is: optional>
        mark-on-success: True                   # <default: False; type: boolean; is: optional>
        mark-on-failure: True                   # <default: False; type: boolean; is: optional>
        break_on_match: True                    # <default: True; type: boolean; is: optional>
        field_extraction_patterns:              # <type: [string,list]; is: required>
          httpd_access_log: ['(?P<httpd_access_log>.*)', 're.MULTILINE | re.DOTALL', 'findall']

#####UrlParser

Parse and extract url parameters.

Configuration example:

    - module: UrlParser
      configuration:
        source-field: uri       # <type: string; is: required>

#####XPathParser

Parse an xml string via xpath.

Configuration example:

    - module: XPathParser
      configuration:
        source-field: 'xml_data'                                # <type: string; is: required>
        query:  '//Item[@%(server_name)s]/@NodeDescription'     # <type: string; is: required>