# -*- coding: utf-8 -*-
from tornado.web import UIModule
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter
import collections

class ServerConfiguration(UIModule):
    def render(self, webserver_module, render_type="text"):
        print self.__dict__
        if render_type == "text":
            return self.render_string("server_configuration_text.html", node=node)
        else:
            return self.render_string("server_configuration_graph.html", node=node)

    def getServerConfiguration(self, webserver_module):
        modules_info = collections.OrderedDict()
        for module_id, module_info in sorted(webserver_module.gp.modules.items(), key=lambda x: x[1]['idx']):
            modules_info[module_id] = {'id': module_id, 'type': module_info['type'], 'configuration': module_info['configuration']}