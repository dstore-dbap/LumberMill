# -*- coding: utf-8 -*-
from tornado.web import UIModule

class ServerListItem(UIModule):
    def render(self, server_name):
        return self.render_string("server_list_item.html", server_name=server_name)