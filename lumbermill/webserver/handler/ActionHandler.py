# -*- coding: utf-8 -*-
import os
import time
import socket
import psutil
import collections
import subprocess
import pprint
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
        cluster_info = self.webserver_module.lumbermill.getModuleInfoById('Cluster')
        if cluster_info:
            cluster_module = cluster_info['instances'][0]
            if cluster_module.leader:
                return
            self.set_header("Access-Control-Allow-Origin", "http://%s:%s" % (cluster_module.getDiscoveredLeader().getHostName(), cluster_module.getDiscoveredLeader().getPort()))
            self.set_header("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
            self.set_header("Access-Control-Allow-Headers","Content-Type, Depth, User-Agent, X-File-Size, X-Requested-With,\
                                                            X-Requested-By, If-Modified-Since, X-File-Name, Cache-Control")

    def __get_current_user(self):
        user_json = self.get_secure_cookie("lumbermill_web")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)

class GetServerStatistics(BaseHandler):

    statistic_counter = {'events_received': 0}

    """
    This will only work, if the statistic module is configured for the running LumberMill.
    """
    def receiveRateStatistics(self, statistic_module):
        self.statistic_counter['events_received'] += statistic_module.getLastReceiveCount()
        return {'timestamp': time.time(), 'received': self.statistic_counter['events_received']}

    def eventTypeStatistics(self, statistic_module):
        event_type_counter = {}
        for event_type, count in sorted(statistic_module.getLastEventTypeCounter().items()):
            try:
                self.statistic_counter['event_type'] += count
            except KeyError:
                self.statistic_counter['event_type'] = count
            event_type_counter.update({'timestamp': time.time(),
                                       'event_type': event_type,
                                       'count': self.statistic_counter['event_type']})
        return event_type_counter

    def eventsInQueuesStatistics(self, statistic_module):
        event_queue_counter = {}
        for module_name, queue_size in sorted(statistic_module.getEventsInQueuesCounter().items()):
            event_queue_counter.update({'timestamp': time.time(),
                                        'module_name': module_name,
                                        'queue_size': queue_size})
        return event_queue_counter

    def get(self):
        # Try to get the statistics module
        stat_module_id = self.webserver_module.getConfigurationValue('statistic_module_id')
        statistic_module_info = self.webserver_module.lumbermill.getModuleInfoById(stat_module_id)
        if not statistic_module_info:
            return
        statistic_data = {}
        statistic_module = statistic_module_info['instances'][0]
        if statistic_module.getConfigurationValue('receive_rate_statistics'):
            statistic_data['receive_rate_statistics'] = self.receiveRateStatistics(statistic_module)
        if statistic_module.getConfigurationValue('waiting_event_statistics'):
            statistic_data['waiting_event_statistics'] = self.eventsInQueuesStatistics(statistic_module)
        if statistic_module.getConfigurationValue('event_type_statistics'):
            statistic_data['event_type_statistics'] = self.eventTypeStatistics(statistic_module)
        if statistic_module.getConfigurationValue('process_statistics'):
            statistic_data['process_statistics'] = statistic_module.getProcessStatistics()
        self.write(tornado.escape.json_encode(statistic_data))

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
                                                'configuration': self.webserver_module.lumbermill.configuration}))

class GetServerConfiguration(BaseHandler):
    def get(self):
        modules_info = collections.OrderedDict()
        for module_id, module_info in sorted(self.webserver_module.lumbermill.modules.items(), key=lambda x: x[1]['idx']):
            modules_info[module_id] = {'id': module_id, 'type': module_info['type'], 'configuration': module_info['configuration']}
        self.write(tornado.escape.json_encode(modules_info))

class RestartHandler(BaseHandler):
    def get(self):
        self.add_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.write(tornado.escape.json_encode({'restart': True}))
        self.flush()
        self.webserver_module.lumbermill.restart()

class AuthLoginHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument("openid.mode", None):
            user = yield self.get_authenticated_user()
            self.set_secure_cookie("lumbermill_web",tornado.escape.json_encode(user))
            self.redirect("/")
            return
        self.authenticate_redirect(ax_attrs=["name"])

class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("lumbermill_web")
        self.write("You are now logged out")
