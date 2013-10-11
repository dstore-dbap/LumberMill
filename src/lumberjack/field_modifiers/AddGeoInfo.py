import BaseModule
import socket

try:
    import GeoIP 
except:
    try:
        import pygeoip
    except:
        pass

class AddGeoInfo(BaseModule.BaseModule):
    """Add country_code and longitude-latitude fields based  on a geoip lookup for a given ip address.
    Configuration example:

    - module: AddGeoInfo
      configuration:
        geoip_dat_path: /usr/share/GeoIP/GeoIP.dat
        lookup_fields: [x_forwarded_for, remote_ip]
    """

    def configure(self, configuration):
        # Call parent configure method
        super(AddGeoInfo, self).configure(configuration)
        self.gi = False
        try:
            self.gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
        except: 
            if 'geoip_dat_path' not in configuration:
                self.logger.error("Will not start module %s since 'geoip_dat_path' not configured." % (self.__class__.__name__))
                self.shutDown()
                return False
            try:
                self.gi = pygeoip.GeoIP(configuration['geoip_dat_path'], pygeoip.MEMORY_CACHE)
            except NameError:
                self.logger.error("Will not start module %s since neiter GeoIP nor pygeoip module could be found." % (self.__class__.__name__))
                self.shutDown()
                return False
        try:
            self.lookup_fields = configuration['lookup_fields']
            if self.lookup_fields.__len__ == 0:
                raise KeyError
        except KeyError:
            self.logger.error("Will not start module %s since lookup_fields not set in configuration. Please set a least one field to use for geoip lookup." % (self.__class__.__name__))
            self.shutDown()
            return False

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
                message_data['longitude-latitude'] = (address_geo_info['longitude'], address_geo_info['latitude'])
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