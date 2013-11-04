# -*- coding: utf-8 -*-
import BaseThreadedModule
import socket
from Decorators import ModuleDocstringParser

try:
    import GeoIP 
except:
    try:
        import pygeoip
    except:
        pass

@ModuleDocstringParser
class AddGeoInfo(BaseThreadedModule.BaseThreadedModule):
    """
    Add country_code and longitude-latitude fields based  on a geoip lookup for a given ip address.

    Configuration example:

    - module: AddGeoInfo
      configuration:
        geoip_dat_path: /usr/share/GeoIP/GeoIP.dat          # <type: string; is: required>
        source_fields: ["x_forwarded_for", "remote_ip"]     # <default: ["x_forwarded_for", "remote_ip"]; type: list; is: optional>
      receivers:
        - NextModule
    """

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.gi = False
        try:
            self.gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
        except: 
            try:
                self.gi = pygeoip.GeoIP(configuration['geoip_dat_path'], pygeoip.MEMORY_CACHE)
            except NameError:
                self.logger.error("Will not start module %s since neiter GeoIP nor pygeoip module could be found." % (self.__class__.__name__))
                self.gp.shutDown()
                return False

    def handleData(self, event):
        hostname_or_ip = False
        for lookup_field in self.getConfigurationValue('source_fields'):
            if lookup_field not in event:
                continue
            hostname_or_ip = event[lookup_field]
            if not hostname_or_ip or hostname_or_ip == "-":
                yield event
                return
            if self.is_valid_ipv4_address(hostname_or_ip) or self.is_valid_ipv6_address(hostname_or_ip):
                lookup_type = "ip_address"
            else:
                lookup_type = "host"
     
            if lookup_type == "ip_address":
                try:
                    address_geo_info = self.gi.record_by_addr(hostname_or_ip);
                except Exception,e:
                    self.logger.debug("lookup for %s failed with error: %s" % (hostname_or_ip, e))
            else:
                try:
                    address_geo_info = self.gi.record_by_name(hostname_or_ip);
                except:
                    self.logger.debug("lookup for %s failed with error: %s" % (hostname_or_ip, e))
            try:
                event['country_code'] = address_geo_info['country_code']
                event['longitude-latitude'] = (address_geo_info['longitude'], address_geo_info['latitude'])
                yield event
                return
            except:
                pass
        # Return message date if lookup failed completely
        yield event
    
    def is_valid_ipv4_address(self, address):
        try:
            addr= socket.inet_pton(socket.AF_INET, address)
        except AttributeError: 
            try:
                addr= socket.inet_aton(address)
            except socket.error:
                return False
            return address.count('.') == 3
        except socket.error: 
            return False
        return True
    
    def is_valid_ipv6_address(self, address):
        try:
            addr= socket.inet_pton(socket.AF_INET6, address)
        except socket.error: 
            return False
        return True