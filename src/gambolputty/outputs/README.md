Output modules
==========

#####ElasticSearchOutput

Store the data dictionary in an elasticsearch index.

The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
Requests will the be loadbalanced via round robin.

Configuration example:

    - module: ElasticSearchOutput
        configuration:
          nodes: ["es-01.dbap.de:9200"]             # <type: list, is: required>
          index-prefix: agora_access-               # <default: 'gambolputty-'; type: string, is: optional>
          index-name: "Fixed index name"            # <default: False; type: string, is: optional>
          store-data-interval: 50                   # <default: 50; type: integer, is: optional>
          store-data-idle: 1                        # <default: 1; type: integer, is: optional>

#####StdOutHandler

Print the data dictionary to stdout.

Configuration example:

    - module: StdOutHandler
      configuration:
        pretty-print: True      # <default: True; type: boolean; is: optional>