# -*- coding: utf-8 -*-
import socket
import os
import psutil
import collections
import subprocess
import tornado.web
import tornado.escape
import tornado.auth
import tornado.gen

class BaseHandler(tornado.web.RequestHandler):
    @property
    def webserver_module(self):
        return self.settings['TornadoWebserver']

    def set_default_headers(self):
        # If we are a pack follower, allow leader to access these handlers.
        cluster_info = self.webserver_module.gp.getModuleInfoById('Cluster')
        if cluster_info:
            cluster_module = cluster_info['instances'][0]
            if cluster_module.leader:
                return
            self.set_header("Access-Control-Allow-Origin", "http://%s:%s" % (cluster_module.getDiscoveredLeader().getHostName(), cluster_module.getDiscoveredLeader().getPort()))
            self.set_header("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
            self.set_header("Access-Control-Allow-Headers","Content-Type, Depth, User-Agent, X-File-Size, X-Requested-With,\
                                                            X-Requested-By, If-Modified-Since, X-File-Name, Cache-Control")

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
            try:
                # When running with pypy, check for missing os.statvfs module. (https://bugs.pypy.org/issue833)
                os.statvfs
                du = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.mountpoint] = {'total': du.total, 'used': du.used, 'free': du.free, 'percent': du.percent}
            except AttributeError:
                # Use fallback.
                df = subprocess.Popen(["df", partition.mountpoint], stdout=subprocess.PIPE)
                output = df.communicate()[0]
                device, size, used, available, percent, mountpoint = output.split("\n")[1].split()
                disk_usage[partition.mountpoint] = {'total': int(size)*1024, 'used': int(used)*1024, 'free': int(available)*1024, 'percent': percent}
        try:
            cpu_count = psutil.NUM_CPUS
        except AttributeError:
            cpu_count = psutil.cpu_count()
        self.write(tornado.escape.json_encode({ 'hostname': socket.gethostname(),
                                                'cpu_count': cpu_count,
                                                'load': os.getloadavg(),
                                                'memory': {'total': mem.total, 'used': mem.used, 'available': mem.available, 'percent': mem.percent},
                                                'disk_usage': disk_usage,
                                                'configuration': self.webserver_module.gp.configuration}))

class GetServerConfiguration(BaseHandler):
    def get(self):
        modules_info = collections.OrderedDict()
        for module_id, module_info in sorted(self.webserver_module.gp.modules.items(), key=lambda x: x[1]['idx']):
            modules_info[module_id] = {'id': module_id, 'type': module_info['type'], 'configuration': module_info['configuration']}
        self.write(tornado.escape.json_encode(modules_info))

class RestartHandler(BaseHandler):
    def get(self):
        self.add_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.write(tornado.escape.json_encode({'restart': True}))
        self.flush()
        self.webserver_module.gp.restart()

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