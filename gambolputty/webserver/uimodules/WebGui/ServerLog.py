# -*- coding: utf-8 -*-
from tornado.web import UIModule

class ServerLog(UIModule):
    def render(self, node):
        return self.render_string("server_log.html", node=node)