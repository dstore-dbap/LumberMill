# -*- coding: utf-8 -*-
import tornado.web
import tornado.escape
import tornado.websocket
import tornado.gen

class BaseHandler(tornado.web.RequestHandler):
    @property
    def WebGui(self):
        return self.settings['WebGui']

    def __get_current_user(self):
        user_json = self.get_secure_cookie("gambolputty_web")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)

class StatisticsWebSocketHandler(tornado.websocket.WebSocketHandler, BaseHandler):
    """
    Redirect the output of the statistics module to a websocket.
    This will only work, if the statistic module is configured for the running GambolPutty.
    """

    def open(self):
        # Try to get the statistics module
        statistic_module_info = self.WebGui.gp.getModuleByName('Statistics')
        if not statistic_module_info:
            self.write_message(tornado.escape.json_encode(False))
            return
        self.statistic_module = statistic_module_info['instances'][0]
        self.statistic_module.registerTimedFunction(id(self), self.sendIntervalStatistics)

    def on_message(self, message):
        pass

    def sendIntervalStatistics(self):
        if self.statistic_module.getConfigurationValue('waiting_event_statistics'):
            self.receiveRateStatistics()
        if self.statistic_module.getConfigurationValue('waiting_event_statistics'):
            self.eventsInQueuesStatistics()
        if self.statistic_module.getConfigurationValue('event_type_statistics'):
            self.eventTypeStatistics()

    def receiveRateStatistics(self):
        eps = self.statistic_module.stats_collector.getCounter('eps')
        if not eps:
            eps = 0
        self.write_message(tornado.escape.json_encode({'timestamp': time.time(),
                                                       'eps': eps}))

    def eventTypeStatistics(self):
        for event_type, count in sorted(self.statistic_module.stats_collector.getAllCounters().iteritems()):
            if not event_type.startswith('event_type_'):
                continue
            event_type = event_type.replace('event_type_', '')
            self.write_message(tornado.escape.json_encode({'timestamp': time.time(),
                                                           'event_type': event_type,
                                                           'count': count}))

    def eventsInQueuesStatistics(self):
        if len(self.statistic_module.module_queues) == 0:
            return
        for module_name, queue in self.statistic_module.module_queues.iteritems():
            self.write_message(tornado.escape.json_encode({'timestamp': time.time(),
                                                            'module_name': module_name,
                                                            'queue_size': queue.qsize()}))

    def on_close(self):
        self.statistic_module.unregisterTimedFunction(id(self))