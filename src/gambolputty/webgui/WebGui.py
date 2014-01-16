# -*- coding: utf-8 -*-
import sys
import time
import tornado.websocket
import tornado.web
import tornado.httpserver
import tornado.autoreload
import tornado.ioloop
import socket
import os.path
import BaseThreadedModule
import Decorators
import Utils
import handler.ActionHandler
import handler.HtmlHandler
import handler.WebsocketHandler
import uimodules.ServerListItem

@Decorators.ModuleDocstringParser
class WebGui(BaseThreadedModule.BaseThreadedModule):
    """
    A WebGui plugin for GambolPutty. At the moment this is just a stub.

    Configuration example:

    - module: WebGui
      port: 6060                 # <default: 5100; type: integer; is: optional>
      document_root: other_root  # <default: 'docroot'; type: string; is: optional>
    """
    module_type = "stand_alone"
    """Set module type"""

    can_run_parallel = False

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.server = False
        self.settings = self.getSettings()
        self.handlers = self.getHandlers()
        self.application = tornado.web.Application(self.handlers, **self.settings)

    def getSettings(self):
        base_path = self.getConfigurationValue('document_root')
        if base_path == 'docroot':
            base_path = "%s/docroot" % os.path.dirname(__file__)
        settings =  {'template_path' : "%s/templates" % base_path,
                     'static_path': "%s/static" % base_path,
                     'ui_modules': uimodules.ServerListItem,
                     'debug': True,
                     'WebGui': self}
        return settings

    def getHandlers(self):
        handlers =  [# HtmlHandler
                     (r"/", handler.HtmlHandler.MainHandler),
                     # StaticFilesHandler
                     (r"/images/(.*)",tornado.web.StaticFileHandler, {"path": "%s/images/" % self.settings['static_path']}),
                     (r"/css/(.*)",tornado.web.StaticFileHandler, {"path": "%s/css/" % self.settings['static_path']}),
                     (r"/js/(.*)",tornado.web.StaticFileHandler, {"path": "%s/js/" % self.settings['static_path']},),
                     # ActionHandler
                     (r"/actions/restart", handler.ActionHandler.RestartHandler),
                     (r"/actions/get_server_info", handler.ActionHandler.GetServerInformation),
                     # WebsocketHandler
                     (r"/websockets/statistics", handler.WebsocketHandler.StatisticsWebSocketHandler)]
        return handlers

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
        return
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