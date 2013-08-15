import BaseModule
import socket
import time
try:
    import GeoIP 
except:
    import pygeoip

class AddGeoInfo(BaseModule.BaseModule):

    def configure(self, configuration):
        self.gi = False
        try:
            self.gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
        except: 
            if 'geoip_dat_path' in configuration:
                self.gi = pygeoip.GeoIP(configuration['geoip_dat_path'], pygeoip.MEMORY_CACHE)
        if not self.gi:
            raise Exception
        try:
            self.lookup_fields = configuration['lookup_fields']
            if self.lookup_fields.__len__ == 0:
                raise KeyError
        except KeyError:
            self.logger.error("lookup_fields not set in configuration. Please set a least one field to use for geoip lookup.")
            self.lj.shutDown()
                        
    def handleData(self, message_data):
        hostname_or_ip = False
        for lookup_field in self.lookup_fields:
            if lookup_field not in message_data:
                continue
            hostname_or_ip = message_data[lookup_field]
            if not hostname_or_ip or hostname_or_ip == "-":
                return message_data
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
                message_data['country_code'] = address_geo_info['country_code']
                message_data['longitude'] = address_geo_info['longitude']
                message_data['latitude'] = address_geo_info['latitude']
                return message_data
            except:
                pass
        # Return message date if lookup failed completely
        return message_data
    
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