# -*- coding: utf-8 -*-
from tornado.web import UIModule

class ServerListItem(UIModule):
    def render(self, node):
        return self.render_string("server_list_item.html", node=node)