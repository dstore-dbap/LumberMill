# -*- coding: utf-8 -*-
import logging
import pprint
import time
import Decorators
import Utils
import sys

class BaseChannel:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.subscribers = []
        self.filters = {}

    def subscribe(self, subscriber):
        if subscriber in self.subscribers:
            return
        self.subscribers.append(subscriber)

    def getFilter(self, receiver_name):
        try:
            return self.filters[receiver_name]
        except KeyError:
            return False

    def setFilter(self, receiver_name, filter):
        self.filters[receiver_name] = filter
        # Replace default sendEvent method with filtered one.
        #print "Setting filter for %s in %s." % (receiver_name, self.__class__.__name__)
        self.sendEvent = self.sendEventFiltered

    def getFilteredReceivers(self, event):
        if not self.filters:
            return self.receivers
        filterd_receivers = {}
        for receiver_name, receiver in self.receivers.iteritems():
            receiver_filter = self.getFilter(receiver_name)
            if not receiver_filter:
                filterd_receivers[receiver_name] = receiver
                continue
            try:
                matched = False
                # If the filter succeeds, the data will be send to the receiver. The filter needs the event variable to work correctly.
                exec receiver_filter
                if matched:
                    filterd_receivers[receiver_name] = receiver
            except:
                raise
        return filterd_receivers

    def publish(self, event):
        #if not self.receivers:
        #    return
        #if len(self.receivers) > 1:
        #    event_clone = event.copy()
        #copy_event = False
        for receiver in self.receivers:
            time.sleep(1)
            for event in receiver.handleEvent(event if copy_event is False else event_clone.copy()):

            """
            try:
                receiver.receiveEvent(event if copy_event is False else event_clone.copy())
            except AttributeError:
                try:
                    receiver.put(event if copy_event is False else event_clone.copy())
                except AttributeError:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("%s%s failed to receive event. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, receiver.__class__.__name__, etype, evalue, Utils.AnsiColors.ENDC))
            """
            copy_event = True