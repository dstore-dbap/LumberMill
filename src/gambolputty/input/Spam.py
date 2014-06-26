# -*- coding: utf-8 -*-
import Utils
import BaseThreadedModule
import time
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class Spam(BaseThreadedModule.BaseThreadedModule):
    """
    Emits events as fast as possible.

    Use this module to load test GambolPutty.

    event: Send custom event data.
    sleep: Time to wait between sending events.
    events_count: Only send configured number of events. 0 means no limit.

    Configuration example:

    - Spam:
        event:                    # <default: {}; type: dict; is: optional>
        sleep:                    # <default: 0; type: int||float; is: optional>
        events_count:             # <default: 0; type: int; is: optional>
        receivers:
          - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_parallel = True

    def run(self):
        counter = 0
        max_events_count = self.getConfigurationValue("events_count")
        event_data = {  '@timestamp': '2014-06-25T08:16:13.805706',
                        'bytes_sent': 14379,
                        'cookie_sid': 'sifa99a95cf9d5aead45d78ffe76e5f3',
                        'cookie_unique_id': '6484505132428a33b90f45a1131336',
                        'country_code': 'DE',
                        'country_name': 'Germany',
                        'data': '<133>Jun 24 14:24:48 lb1 nginx: httpd[25773] www.titus.de 62.225.111.26 0.1336 "GET /product-images/overlay/Venom/Longboard-Rolle/Thug+Passion+80A_780451.jpg HTTP/1.1" 200 14379 sifa99a95cf9d5aead45d78ffe76e5f3 6484505132428a33b90f45a1131336 "http://www.titus.de/Skateboard/Longboards/Longboard-Rollen.html" "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 7 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.141 Safari/537.36"',
                        'geoip': [9.0, 51.0],
                        'host': 'lb1',
                        'http_method': 'GET',
                        'http_status': 200,
                        'http_status_mapped': 'OK',
                        'log_timestamp': 'Jun 24 14:24:48',
                        'params': {   },
                        'parsed_url': {   'params': '',
                                          'path': u'/product-images/overlay/Venom/Longboard-Rolle/Thug+Passion+80A_780451.jpg',
                                          'query': '',
                                          'scheme': ''},
                        'pid': 25773,
                        'referer': 'http://www.titus.de/Skateboard/Longboards/Longboard-Rollen.html',
                        'remote_ip': '62.225.111.26',
                        'request_time': 133,
                        'server_type': 'nginx',
                        'syslog_prival': '<133>',
                        'time_zone': 'Europe/Berlin',
                        'uri': '/product-images/overlay/Venom/Longboard-Rolle/Thug+Passion+80A_780451.jpg',
                        'user_agent': 'Mozilla/5.0 (Linux; Android 4.4.2; Nexus 7 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.141 Safari/537.36',
                        'user_agent_info': {   'bot': False,
                                               'browser': {   'name': 'Chrome',
                                                              'version': '35.0.1916.141'},
                                               'dist': {   'name': 'Android', 'version': '4.4.2'},
                                               'os': {   'name': 'Linux'},
                                               'platform': {   'name': 'Android',
                                                               'version': '4.4.2'}},
                        'virtual_host_name': 'www.titus.de'}

        while self.alive:
            event = Utils.getDefaultEventDict(self.getConfigurationValue("event"), caller_class_name=self.__class__.__name__) # self.getConfigurationValue("event")
            self.sendEvent(event)
            if self.getConfigurationValue("sleep"):
                time.sleep(self.getConfigurationValue("sleep"))
            counter += 1
            if (counter - max_events_count == 0):
                self.gp.shutDown()
