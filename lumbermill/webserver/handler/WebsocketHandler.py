# -*- coding: utf-8 -*-
import tornado.web
import tornado.escape
import tornado.websocket
import tornado.gen
import logging
import time


class WebsocketLoggingHandler(logging.Handler):
    """
    A handler class which allows to log to a websocket.
    """

    def __init__(self, websocket_handler):
        logging.Handler.__init__(self)
        self.websocket_handler = websocket_handler
        self.formatter = None

    def emit(self, record):
        try:
            msg = self.format(record)
            self.websocket_handler.write_message(tornado.escape.json_encode({'timestamp': time.time(),
                                                                             'log_message': msg}))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

class BaseHandler(tornado.web.RequestHandler):
    @property
    def webserver_module(self):
        return self.settings['TornadoWebserver']

    def __get_current_user(self):
        user_json = self.get_secure_cookie("gambolputty_web")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)

class LogToWebSocketHandler(tornado.websocket.WebSocketHandler, BaseHandler):
    def open(self):
        # Create new log handler.
        self.ws_stream_handler = WebsocketLoggingHandler(self)
        # Get all configured modules and register our log handler.
        for module_name, module_info in sorted(self.webserver_module.gp.modules.items(), key=lambda x: x[1]['idx']):
            for instance in module_info['instances']:
                instance.logger.addHandler(self.ws_stream_handler)

    def on_close(self):
        # Get all configured modules and unregister our log handler.
        for module_name, module_info in sorted(self.webserver_module.gp.modules.items(), key=lambda x: x[1]['idx']):
            for instance in module_info['instances']:
                instance.logger.removeHandler(self.ws_stream_handler)

class StatisticsWebSocketHandler(tornado.websocket.WebSocketHandler, BaseHandler):
    """
    Redirect the output of the statistics module to a websocket.
    This will only work, if the statistic module is configured for the running LumberMill.
    """
    def open(self):
        # Try to get the statistics module
        statistic_module_info = self.webserver_module.gp.getModuleInfoById('Statistics')
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
        for event_type, count in sorted(self.statistic_module.stats_collector.getAllCounters().items()):
            if not event_type.startswith('event_type_'):
                continue
            event_type = event_type.replace('event_type_', '')
            self.write_message(tornado.escape.json_encode({'timestamp': time.time(),
                                                           'event_type': event_type,
                                                           'count': count}))

    def eventsInQueuesStatistics(self):
        if len(self.statistic_module.module_queues) == 0:
            return
        for module_name, queue in self.statistic_module.module_queues.items():
            self.write_message(tornado.escape.json_encode({'timestamp': time.time(),
                                                            'module_name': module_name,
                                                            'queue_size': queue.qsize()}))

    def on_close(self):
        self.statistic_module.unregisterTimedFunction(id(self))