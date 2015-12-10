# -*- coding: utf-8 -*-
from tornado.web import UIModule

class ServerInfo(UIModule):
    def render(self, node):
        return self.render_string("server_info.html", node=node)