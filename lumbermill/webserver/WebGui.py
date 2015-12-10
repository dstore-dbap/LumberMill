# -*- coding: utf-8 -*-
import tornado.web
import handler.ActionHandler
import handler.HtmlHandler
import handler.WebsocketHandler
import uimodules.WebGui.ServerInfo

import lumbermill.Utils as Utils
from lumbermill.BaseModule import BaseModule
from lumbermill.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class WebGui(BaseModule):
    """
    A WebGui plugin for LumberMill. At the moment this is just a stub.

    Module dependencies:    WebserverTornado

    Configuration template:

    tornado_webserver: Name of the webserver module.
    document_root: Path to look for templates and static files.

    - WebGui:
       tornado_webserver: webserver     # <default: 'WebserverTornado'; type: string; is: optional>
       document_root: other_root        # <default: 'docroot'; type: string; is: optional>
    """
    module_type = "stand_alone"
    """Set module type"""

    can_run_forked = False

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.configure(self, configuration)
        # Get tornado webserver module instance.
        mod_info = self.lumbermill.getModuleInfoById(self.getConfigurationValue('tornado_webserver'))
        if not mod_info:
            self.logger.error("Could not start web gui module. Required webserver module %s not found. Please check your configuration." % (self.getConfigurationValue('tornado_webserver')))
            self.lumbermill.shutDown()
            return
        self.webserver_module = mod_info['instances'][0]
        self.webserver_module.addUiModules([uimodules.WebGui.ServerInfo])
        self.webserver_module.addHandlers(self.getHandlers())

    def getHandlers(self):
        settings = self.webserver_module.getSettings()
        handlers =  [# HtmlHandler
                     (r"/", handler.HtmlHandler.MainHandler),
                     (r"/server_configuration", handler.HtmlHandler.ServerConfigurationAsText),
                     (r"/configuration", handler.HtmlHandler.ConfigurationHandler),
                     # StaticFilesHandler
                     (r"/images/(.*)",tornado.web.StaticFileHandler, {"path": "%s/images/" % settings['static_path']}),
                     (r"/css/(.*)",tornado.web.StaticFileHandler, {"path": "%s/css/" % settings['static_path']}),
                     (r"/js/(.*)",tornado.web.StaticFileHandler, {"path": "%s/js/" % settings['static_path']},),
                     # REST ActionHandler
                     (r"/rest/server/restart", handler.ActionHandler.RestartHandler),
                     (r"/rest/server/info", handler.ActionHandler.GetServerInformation),
                     (r"/rest/server/configuration", handler.ActionHandler.GetServerConfiguration),
                     # WebsocketHandler
                     (r"/websockets/statistics", handler.WebsocketHandler.StatisticsWebSocketHandler),
                     (r"/websockets/get_logs", handler.WebsocketHandler.LogToWebSocketHandler)]
        return handlers