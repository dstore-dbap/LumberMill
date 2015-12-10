# -*- coding: utf-8 -*-
import pprint
import tornado.web
import tornado.escape
import socket
import json
import yaml
from pygments import highlight
from pygments.lexers import YamlLexer
from pygments.formatters import HtmlFormatter

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
        nodes = []
        localnode = {'server_name': socket.gethostname(),
                     'server_type': 'StandAlone'}
        # Check if cluster module is available.
        cluster_info = self.webserver_module.gp.getModuleInfoById('Cluster')
        if cluster_info:
            cluster_module = cluster_info['instances'][0]
            localnode['server_type'] = "PackLeader" if cluster_module.leader else "PackMember"
            if cluster_module.leader:
                for pack_member in cluster_module.getPackMembers().itervalues():
                    nodes.append({'server_name': pack_member.getHostName(),
                                  'server_type': "PackLeader" if pack_member.leader else "PackMember"})
        nodes.insert(0, localnode)
        self.render("index.html",
                    page_title="LumberMill WebGui",
                    nodes=nodes,
                    webserver_module=self.webserver_module)

class ServerConfigurationAsText(BaseHandler):
    def get(self):
        config_as_html = highlight(self.webserver_module.gp.getRawConfiguration(), YamlLexer(), HtmlFormatter(noclasses=True))
        self.content_type = 'text/html'
        self.write(config_as_html)

class ConfigurationHandler(BaseHandler):
    def get(self):
        self.render("server_configuration.html",
                    page_title="Server configuration")