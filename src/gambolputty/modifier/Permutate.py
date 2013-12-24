# -*- coding: utf-8 -*-
import Utils
import itertools
import BaseThreadedModule
import Decorators
import Utils
import sys

@Decorators.ModuleDocstringParser
class Permutate(BaseThreadedModule.BaseThreadedModule):
    """
    Creates successive len('target_fields') length permutations of elements in 'source_field'.

    To add some context data to each emitted event 'context_data_field' can specify a field
    containing a dictionary with the values of 'source_field' as keys.

    Configuration example:

    - module: Permutate
      configuration:
        source_field: facets                                                # <type: string; is: required>
        target_fields: ['field1', 'field2']                                 # <type: list; is: required>
        context_data_field: context_data                                    # <default: ""; type:string; is: optional>
        context_target_mapping: {'field1': ['ctx_field1', 'ctx_field2']}    # <default: {}; type: dict; is: optional if context_data_field == "" else required>
      receivers:
        - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        @return data: dictionary
        """

        try:
            context_data = event[self.getConfigurationValue('context_data_field')]
        except KeyError:
            context_data = False
        try:
            permutation_data = event[self.getConfigurationValue('source_field')]
        except KeyError:
            yield event
            return
        if type(permutation_data) is not list:
            yield event
            return
        target_field_names = self.getConfigurationValue('target_fields')
        context_target_mapping = self.getConfigurationValue('context_target_mapping')
        for permutation in itertools.permutations(permutation_data, r=len(target_field_names)):
            event_copy = event.copy()
            if context_data:
                try:
                    # Rewrite the context data keys to new keys in context_target_mapping
                    ctx_data = {}
                    for idx, dct in enumerate([context_data[key] for key in permutation if key in context_data]):
                        for mapping_key, newkeys in context_target_mapping.iteritems():
                            if mapping_key in dct:
                               ctx_data[newkeys[idx]] = dct[mapping_key]
                    event_copy.update(ctx_data)
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.warning("%sCould not add context data. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, etype, evalue, Utils.AnsiColors.ENDC))
            perm = dict(zip(target_field_names, permutation))
            event_copy.update(perm)
            yield event_copy