# -*- coding: utf-8 -*-
import socket
import sys
import pygeoip

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser, memoize


@ModuleDocstringParser
class AddGeoInfo(BaseThreadedModule):
    """
    Add country_code and longitude-latitude fields based  on a geoip lookup for a given ip address.

    Here an example of fields that the module provides:
    {'city': 'Hanover', 'region_name': '06', 'area_code': 0, 'time_zone': 'Europe/Berlin', 'dma_code': 0, 'metro_code': None, 'country_code3': 'DEU', 'latitude': 52.36670000000001, 'postal_code': '', 'longitude': 9.716700000000003, 'country_code': 'DE', 'country_name': 'Germany', 'continent': 'EU'}

    geoip_dat_path: path to maxmind geoip database file.
    source_fields: list of fields to use for lookup. The first list entry that produces a hit is used.
    target: field to populate with the geoip data. If none is provided, the field will be added directly to the event.
    geo_info_fields: fields to add. Available field names:
     - area_code
     - city
     - continent
     - country_code
     - country_code3
     - country_name
     - dma_code
     - metro_code
     - postal_code
     - region_name
     - time_zone
     - latitude
     - longitude

    Configuration template:

    - AddGeoInfo:
       geoip_dat_path:                  # <type: string; is: required>
       geo_info_fields:                 # <default: None; type: list; is: optional>
       source_fields:                   # <default: ["x_forwarded_for", "remote_ip"]; type: list; is: optional>
       target_field:                    # <default: None; type: None||string; is: optional>
       receivers:
        - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.gi = False
        try:
            self.gi = pygeoip.GeoIP(configuration['geoip_dat_path'], pygeoip.MEMORY_CACHE)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not init %s. Exception: %s, Error: %s. " % (self.__class__.__name__, etype, evalue))
        if not self.gi:
            self.lumbermill.shutDown()
            return False
        self.geo_info_fields = self.getConfigurationValue('geo_info_fields')
        self.source_fields = self.getConfigurationValue('source_fields')
        self.target_field = self.getConfigurationValue('target_field')

    def getStartMessage(self):
        """
        Return the module name.
        """
        return "from %s to %s" % (self.source_fields, self.target_field)


    def handleEvent(self, event):
        for lookup_field_name in self.source_fields:
            try:
                lookup_field_name_value = event[lookup_field_name]
            except KeyError:
                continue
            if not lookup_field_name_value or lookup_field_name_value == "-":
                continue
            if isinstance(lookup_field_name_value, str):
                geo_info_fields = self.getGeoIpInfo(lookup_field_name_value)
            elif isinstance(lookup_field_name_value, list):
                for field_value in lookup_field_name_value:
                    geo_info_fields = self.getGeoIpInfo(field_value)
                    if geo_info_fields:
                        break
            if geo_info_fields:
                if self.target_field:
                    event[self.target_field] = geo_info_fields
                else:
                    event.update(geo_info_fields)
                break
        yield event

    @memoize
    def getGeoIpInfo(self, hostname_or_ip):
        all_geo_info_fields = {}
        if self.is_valid_ipv4_address(hostname_or_ip) or self.is_valid_ipv6_address(hostname_or_ip):
            lookup_type = "ip_address"
        else:
            lookup_type = "host"
        if lookup_type == "ip_address":
            try:
                all_geo_info_fields = self.gi.record_by_addr(hostname_or_ip)
            except Exception,e:
                pass
        else:
            try:
                all_geo_info_fields = self.gi.record_by_name(hostname_or_ip)
            except:
                pass
        if not self.geo_info_fields:
            return all_geo_info_fields
        configured_geo_info_fields = {}
        for field_name in self.geo_info_fields:
            try:
                configured_geo_info_fields[field_name] = all_geo_info_fields[field_name]
            except:
                pass
        return configured_geo_info_fields


    def is_valid_ipv4_address(self, address):
        try:
            addr = socket.inet_pton(socket.AF_INET, address)
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