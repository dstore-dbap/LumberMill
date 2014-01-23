# -*- coding: utf-8 -*-
import sys
import time
import tornado.web
import tornado.httpserver
import tornado.autoreload
import tornado.ioloop
import socket
import os.path
import BaseThreadedModule
import Decorators
import Utils
import uimodules.ServerListItem

@Decorators.ModuleDocstringParser
class WebserverTornado(BaseThreadedModule.BaseThreadedModule):
    """
    A tornado based web server.

    Configuration example:

    - module: WebserverTornado
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
        self.application = tornado.web.Application([], **self.settings)

    def addHandlers(self, host_handlers=[], host_pattern='.*$'):
        self.application.add_handlers(host_pattern, host_handlers)

    def getSettings(self):
        base_path = self.getConfigurationValue('document_root')
        if base_path == 'docroot':
            base_path = "%s/docroot" % os.path.dirname(__file__)
        settings =  {'template_path' : "%s/templates" % base_path,
                     'static_path': "%s/static" % base_path,
                     'ui_modules': uimodules.ServerListItem,
                     'debug': False,
                     'TornadoWebserver': self}
        return settings

    def run(self):
        try:
            self.server = tornado.httpserver.HTTPServer(self.application)
            self.server.listen(self.getConfigurationValue('port'))
            for fd, server_socket in self.server._sockets.iteritems():
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not start webserver on %s. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue('port'), etype, evalue, Utils.AnsiColors.ENDC))
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

    def shutDown(self, silent):
        # Call parent shutDown method.
        BaseThreadedModule.BaseThreadedModule.shutDown(self, silent)
        if self.server:
            self.server.stop()
            # Give os time to free the socket. Otherwise a reload will fail with 'address already in use'
            time.sleep(.2)