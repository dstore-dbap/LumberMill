# -*- coding: utf-8 -*-
import pprint
import sys
import time
import tornado.ioloop
import tornado.web
import tornado.auth
import tornado.escape
import tornado.template
import tornado.httpserver
import tornado.websocket
from tornado import gen
import socket
import os.path
import BaseThreadedModule
import Decorators
import Utils

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
        Redirect the output of the statistics module to a websocket if it is configured.
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

class MainHandler(BaseHandler):
    def get(self):
        self.render(
                "index.html",
                page_title="GambolPutty WebGui",
                header_text="Welcome",
                footer_text="You've landed on my amazing page here."
        )

class RestartHandler(BaseHandler):
    def get(self):
        self.render(
                "index.html",
                page_title="GambolPutty WebGui",
                header_text="Welcome",
                footer_text="You've landed on my amazing page here."
        )
        self.WebGui.gp.restart()

class AuthLoginHandler(BaseHandler, tornado.auth.GoogleMixin):
    @gen.coroutine
    def get(self):
        if self.get_argument("openid.mode", None):
            user = yield self.get_authenticated_user()
            self.set_secure_cookie("gambolputty_web",tornado.escape.json_encode(user))
            self.redirect("/")
            return
        self.authenticate_redirect(ax_attrs=["name"])

class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("gambolputty_web")
        self.write("You are now logged out")

@Decorators.ModuleDocstringParser
class WebGui(BaseThreadedModule.BaseThreadedModule):
    """
    A WebGui plugin for GambolPutty. At the moment this is just a stub.

    Configuration example:

    - module: WebGui
      port: 6060                 # <default: 5100; type: integer; is: optional>
      document_root: other_root  # <default: 'webgui_docroot'; type: string; is: optional>
    """
    module_type = "stand_alone"
    """Set module type"""

    can_run_parallel = False

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        base_path = self.getConfigurationValue('document_root')
        if base_path == 'webgui_docroot':
            base_path = "%s/../webgui_docroot" % os.path.dirname(__file__)

        handlers = [(r"/", MainHandler),
                    (r"/restart", RestartHandler),
                    (r"/websockets/statistics", StatisticsWebSocketHandler)]

        settings = {'template_path' : "%s/templates" % base_path,
                    'static_path': "%s/static" % base_path,
                    'debug': True,
                    'WebGui': self}
        self.application = tornado.web.Application(handlers, **settings)

    def run(self):
        try:
            self.server = tornado.httpserver.HTTPServer(self.application)
            self.server.listen(self.getConfigurationValue('port'))
            for fd, server_socket in self.server._sockets.iteritems():
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not start webgui on %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue('port'), etype, evalue, Utils.AnsiColors.ENDC))
            return
        tornado.autoreload.add_reload_hook(self.shutDown)
        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.make_current()
        try:
            ioloop.start()
        except ValueError:
            # Ignore errors like "ValueError: I/O operation on closed kqueue fd". These might be thrown during a reload.
            pass

    def shutDown(self):
        # Call parent shutDown method.
        BaseThreadedModule.BaseThreadedModule.shutDown(self)
        if self.server:
            self.server.stop()
            # Give os time to free the socket. Otherwise a reload will fail with 'address already in use'
            time.sleep(.2)