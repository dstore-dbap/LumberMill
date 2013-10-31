Output modules
==========

#####ElasticSearchOutput

Store the data dictionary in an elasticsearch index.

The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
Requests will the be loadbalanced via round robin.

Configuration example:

    - module: ElasticSearchOutput
        configuration:
          nodes: ["es-01.dbap.de:9200"]             # <type: list; is: required>
          index_prefix: agora_access-               # <default: 'gambolputty-'; type: string; is: optional>
          index_name: "Fixed index name"            # <default: ""; type: string; is: optional>
          store_data_interval: 50                   # <default: 50; type: integer; is: optional>
          store_data_idle: 1                        # <default: 1; type: integer; is: optional>
      receivers:
        - NextModule

#####StdOutHandler

Print the data dictionary to stdout.

Configuration example:

    - module: StdOutHandler
      configuration:
        pretty_print: True      # <default: True; type: boolean; is: optional>