# -*- coding: utf-8 -*-
import Utils
import BaseThreadedModule
import Decorators

@Decorators.ModuleDocstringParser
class Facet(BaseThreadedModule.BaseThreadedModule):
    """
    Collect different values of one field over a defined period of time and pass all
    encountered variations on as new event after period is expired.

    The event emitted by this module will be of type: "facet" and will have a "facets" and a "context_data" field.

    Configuration example:

    - module: Facet
      configuration:
        source_field: url                        # <type:string; is: required>
        group_by: %(remote_ip)s                  # <type:string; is: required>
        keep_fields: [user_agent]                # <default: []; type: list; is: optional>
        interval: 30                             # <default: 5; type: float||integer; is: optional>
      receivers:
        - NextModule
    """

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.facet_data = {}
        func = self.getEvaluateFunc()
        func(self)

    def getEvaluateFunc(self):
        @Decorators.setInterval(self.getConfigurationValue('interval'))
        def evaluateFacets(self):
            if not self.facet_data:
              return
            self.logger.info("Sending facet event...")
            for key, facet_data in self.facet_data.iteritems():
                event = Utils.getDefaultDataDict({'event_type': 'facet',
                                                  'facets': facet_data['facets'],
                                                  'context_data': facet_data['context_data']})
                self.addEventToOutputQueues(event)
            self.facet_data = {}

        return evaluateFacets

    def handleData(self, data):
        """
        Process the event.

        @param data: dictionary
        @return data: dictionary
        """
        try:
            facet_value = data[self.getConfigurationValue('source_field')]
        except KeyError:
            yield data
        key = self.getConfigurationValue('group_by', data)
        try:
            facet_info = self.facet_data[key]
        except KeyError:
            facet_info = self.facet_data[key] = {'context_data': [], 'facets': []}
        if facet_value not in facet_info['facets']:
            keep = {}
            for keep_field in self.getConfigurationValue('keep_fields'):
                try:
                    keep[keep_field] = data[keep_field]
                except KeyError:
                    pass
            self.facet_data[key]['context_data'].append(keep)
            self.facet_data[key]['facets'].append(facet_value)
        yield data
