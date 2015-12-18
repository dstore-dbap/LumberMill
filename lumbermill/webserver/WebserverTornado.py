# -*- coding: utf-8 -*-
import os.path
import socket
import sys
import time

import tornado.autoreload
import tornado.httpserver
import tornado.ioloop
import tornado.web

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class WebserverTornado(BaseThreadedModule):
    """
    A tornado based web server.

    Configuration template:

    - WebserverTornado:
       port:                            # <default: 5100; type: integer; is: optional>
       tls:                             # <default: False; type: boolean; is: optional>
       key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
       cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
       document_root:                   # <default: '../assets/webserver_docroot'; type: string; is: optional>
       application_settings:            # <default: None; type: None||dict; is: optional>
    """
    module_type = "stand_alone"
    """Set module type"""

    can_run_forked = False

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.server = False
        self.settings = self.getSettings()
        self.application = tornado.web.Application([], **self.settings)

    def addHandlers(self, host_handlers=[], host_pattern='.*$'):
        self.application.add_handlers(host_pattern, host_handlers)

    def getSettings(self):
        base_path = self.getConfigurationValue('document_root')
        if base_path == 'docroot':
            base_path = "%s/docroot" % os.path.dirname(__file__)
        settings = {'template_path' : "%s/templates" % base_path,
                    'static_path': "%s/static" % base_path,
                    'ui_modules': [],
                    'debug': False,
                    'TornadoWebserver': self}
        if self.getConfigurationValue('application_settings'):
            settings.update(self.getConfigurationValue('application_settings'))
        return settings

    def addUiModules(self, modules):
        if not isinstance(modules, list):
            modules = [modules]
        for module in modules:
            if module in self.application.settings['ui_modules']:
                continue
            self.application.settings['ui_modules'].append(module)
            self.application._load_ui_modules(module)

    def getUiModule(self, module_name):
        try:
            return self.application.ui_modules[module_name]
        except KeyError:
            return False

    def start(self):
        ssl_options = None
        if self.getConfigurationValue("tls"):
            ssl_options = { 'certfile': self.getConfigurationValue("cert"),
                            'keyfile': self.getConfigurationValue("key")}
        try:
            self.server = tornado.httpserver.HTTPServer(self.application, ssl_options=ssl_options)
            self.server.listen(self.getConfigurationValue('port'))
            for fd, server_socket in self.server._sockets.items():
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not start webserver on %s. Exception: %s, Error: %s." % (self.getConfigurationValue('port'), etype, evalue))
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
        if self.server:
            self.server.stop()
            # Give os time to free the socket. Otherwise a reload will fail with 'address already in use'
            time.sleep(.2)
        # Call parent shutDown method.
        BaseThreadedModule.shutDown(self)
