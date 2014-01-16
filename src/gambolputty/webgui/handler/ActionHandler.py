# -*- coding: utf-8 -*-
import socket
import os
import psutil
import tornado.web
import tornado.escape
import tornado.auth
import tornado.gen

class BaseHandler(tornado.web.RequestHandler):
    @property
    def WebGui(self):
        return self.settings['WebGui']

    def __get_current_user(self):
        user_json = self.get_secure_cookie("gambolputty_web")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)

class GetServerInformation(BaseHandler):
    def get(self):
        mem = psutil.virtual_memory()
        partitions = psutil.disk_partitions()
        disk_usage = {}
        for partition in partitions:
            du = psutil.disk_usage(partition.mountpoint)
            disk_usage[partition.mountpoint] = {'total': du.total, 'used': du.used, 'free': du.free, 'percent': du.percent}
        self.write(tornado.escape.json_encode({ 'hostname': socket.gethostname(),
                                                'cpu_count': psutil.NUM_CPUS,
                                                'load': os.getloadavg(),
                                                'memory': {'total': mem.total, 'used': mem.used, 'available': mem.available, 'percent': mem.percent},
                                                'disk_usage': disk_usage,
                                                'configuration': self.WebGui.gp.configuration}))

class RestartHandler(BaseHandler):
    def get(self):
        self.WebGui.gp.restart()
        self.write(tornado.escape.json_encode({True}))

class AuthLoginHandler(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument("openid.mode", None):
            user = yield self.get_authenticated_user()
            self.set_secure_cookie("gambolputty_web",tornado.escape.json_encode(user))
            self.redirect("/")
            return
        self.authenticate_redirect(ax_attrs=["name"])

class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("gambolputty_web")
        self.write("You are now logged out")