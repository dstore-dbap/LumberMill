import BaseModule
import socket
import time
try:
    import GeoIP 
except:
    import pygeoip

class AddGeoInfo(BaseModule.BaseModule):

    def configure(self, configuration):
        try:
            self.gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
        except: 
            if 'geo_ip_dat' in configuration:
                self.gi = pygeoip.GeoIP(configuration['geo_ip_dat'], pygeoip.MEMORY_CACHE)
            
    def handleData(self, message_data):
        hostname_or_ip = False
        if 'x_forwarded_for' in message_data and message_data['x_forwarded_for'] != "-":
            hostname_or_ip = message_data['x_forwarded_for']
        elif 'remote_ip' in message_data:
            hostname_or_ip = message_data['remote_ip']
        if not hostname_or_ip:
            return message_data
        if self.is_valid_ipv4_address(hostname_or_ip) or self.is_valid_ipv6_address(hostname_or_ip):
            lookup_type = "ip_address"
        else:
            lookup_type = "host"
        
        lookup_failed = False;
        if lookup_type == "ip_address":
            try:
                address_geo_info = self.gi.record_by_addr(hostname_or_ip);
            except:
                lookup_failed = True
        else:
            try:
                address_geo_info = self.gi.record_by_name(hostname_or_ip);
            except:
                lookup_failed = True
        
        try:
            message_data['country_code'] = address_geo_info['country_code']
            message_data['longitude'] = address_geo_info['longitude']
            message_data['latitude'] = address_geo_info['latitude']
        except: 
            pass

        return message_data
    
    def is_valid_ipv4_address(self, address):
        try:
            addr= socket.inet_pton(socket.AF_INET, address)
        except AttributeError: # no inet_pton here, sorry
            try:
                addr= socket.inet_aton(address)
            except socket.error:
                return False
            return address.count('.') == 3
        except socket.error: # not a valid address
            return False
    
        return True
    
    def is_valid_ipv6_address(self, address):
        try:
            addr= socket.inet_pton(socket.AF_INET6, address)
        except socket.error: # not a valid address
            return False
        return True