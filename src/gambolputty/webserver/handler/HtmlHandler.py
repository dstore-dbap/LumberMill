# -*- coding: utf-8 -*-
import tornado.web
import tornado.escape
import socket

class BaseHandler(tornado.web.RequestHandler):
    @property
    def webserver_module(self):
        return self.settings['TornadoWebserver']

    def __get_current_user(self):
        user_json = self.get_secure_cookie("gambolputty_web")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)

class MainHandler(BaseHandler):
    def get(self):
        # Check if cluster module is available.
        server_type = "Master"
        cluster_info = self.webserver_module.gp.getModuleByName('Cluster')
        if cluster_info:
            server_type = "PackLeader" if cluster_info['instances'][0].leader else "PackMember"
        self.render(
                "index.html",
                page_title="GambolPutty WebGui",
                server_name=socket.gethostname(),
                server_type=server_type
        )