# -*- coding: utf-8 -*-
import os
import socket
import sys
import geoip2.database
import geoip2.errors

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser, memoize
from lumbermill.constants import LUMBERMILL_BASEPATH


@ModuleDocstringParser
class AddGeoInfo(BaseThreadedModule):
    """
    Add country_code and longitude-latitude fields based  on a geoip lookup for a given ip address.

    Here an example of fields that the module provides:
    {'city': 'Hanover', 'region_name': '06', 'area_code': 0, 'time_zone': 'Europe/Berlin', 'dma_code': 0, 'metro_code': None, 'country_code3': 'DEU', 'latitude': 52.36670000000001, 'postal_code': '', 'longitude': 9.716700000000003, 'country_code': 'DE', 'country_name': 'Germany', 'continent': 'EU'}

    geoip_dat_path: path to maxmind geoip2 database file.
    asn_dat_path: path to maxmind ASN database file.
    maxmind_locals: List of locale codes. See: https://github.com/maxmind/GeoIP2-python/blob/master/geoip2/database.py#L59
    maxmind_mode: See: https://github.com/maxmind/GeoIP2-python/blob/master/geoip2/database.py#L71
    source_fields: list of fields to use for lookup. The first list entry that produces a hit is used.
    target: field to populate with the geoip data. If none is provided, the field will be added directly to the event.
    maxmind_info_fields: fields to add. Available fields:
     - city
     - postal_code
     - country_name
     - country_code
     - continent_code
     - continent
     - area_code
     - region_name
     - longitude
     - latitude
     - longlat
     - time_zone
     - metro_code
     - autonomous_system_number
     - autonomous_system_organization

    Configuration template:

    - AddGeoInfo:
       geoip_dat_path:                  # <default: './assets/maxmind/GeoLite2-City.mmdb'; type: string; is: optional>
       asn_dat_path:                    # <default: './assets/maxmind/GeoLite2-ASN.mmdb'; type: string; is: optional>
       maxmind_locals:                  # <default: ['en']; type: list; is: optional>
       maxmind_mode:                    # <default: 'MODE_AUTO'; type: string; is: optional; values: ['MODE_MMAP_EXT', 'MODE_MMAP', 'MODE_FILE', 'MODE_MEMORY', 'MODE_AUTO']>
       maxmind_info_fields:             # <default: None; type: None||list; is: optional>
       source_fields:                   # <default: ["x_forwarded_for", "remote_ip"]; type: list; is: optional>
       target_field:                    # <default: "geo_info"; type: string; is: optional>
       receivers:
        - NextModule
    """

    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        allowed_maxmind_fields = ['city', 'postal_code', 'country_name', 'country_code', 'continent_code',
                                  'continent', 'area_code', 'region_name', 'longitude', 'latitude',
                                  'longlat', 'time_zone', 'metro_code', 'autonomous_system_number',
                                  'autonomous_system_organization']
        self.maxmind_info_fields = self.getConfigurationValue('maxmind_info_fields')
        if self.maxmind_info_fields:
            fields_are_valid = True
            for geo_info_field in self.maxmind_info_fields:
                if geo_info_field in allowed_maxmind_fields:
                    continue
                fields_are_valid = False
                self.logger.error('Configured geoip field %s is not valid.' % geo_info_field)
            if not fields_are_valid:
                self.logger.error('Valid fields are: %s' % allowed_maxmind_fields)
                self.lumbermill.shutDown()
        self.source_fields = self.getConfigurationValue('source_fields')
        self.target_field = self.getConfigurationValue('target_field')
        self.geoip_db = self.openGeoIPDatabase()
        if not self.geoip_db:
            self.lumbermill.shutDown()
        self.asn_db = self.openASNDatabase()
        if not self.asn_db:
            self.lumbermill.shutDown()

    def getStartMessage(self):
        """
        Return the module name.
        """
        return "from %s to %s" % (self.source_fields, self.target_field)

    def openGeoIPDatabase(self):
        geoip_dat_path = self.getConfigurationValue('geoip_dat_path')
        if geoip_dat_path == './assets/maxmind/GeoLite2-City.mmdb':
            geoip_dat_path = LUMBERMILL_BASEPATH + '/' + geoip_dat_path
        if not os.path.isfile(geoip_dat_path):
            self.logger.error("Path %s does not point to a valid file. Please check." % geoip_dat_path)
            return
        maxmind_mode = {'MODE_MMAP_EXT': geoip2.database.MODE_MMAP_EXT,
                        'MODE_MMAP': geoip2.database.MODE_MMAP,
                        'MODE_FILE': geoip2.database.MODE_FILE,
                        'MODE_MEMORY': geoip2.database.MODE_MEMORY}.get(self.getConfigurationValue('maxmind_mode'), geoip2.database.MODE_AUTO)
        try:
            return geoip2.database.Reader(geoip_dat_path, locales=self.getConfigurationValue('maxmind_locals'), mode=maxmind_mode)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not init %s. Exception: %s, Error: %s. " % (self.__class__.__name__, etype, evalue))

    def openASNDatabase(self):
        asn_dat_path = self.getConfigurationValue('asn_dat_path')
        if asn_dat_path == './assets/maxmind/GeoLite2-ASN.mmdb':
            asn_dat_path = LUMBERMILL_BASEPATH + '/' + asn_dat_path
        if not os.path.isfile(asn_dat_path):
            self.logger.error("Path %s does not point to a valid file. Please check." % asn_dat_path)
            return
        asn_mode = {'MODE_MMAP_EXT': geoip2.database.MODE_MMAP_EXT,
                    'MODE_MMAP': geoip2.database.MODE_MMAP,
                    'MODE_FILE': geoip2.database.MODE_FILE,
                    'MODE_MEMORY': geoip2.database.MODE_MEMORY}.get(self.getConfigurationValue('maxmind_mode'), geoip2.database.MODE_AUTO)
        try:
            return geoip2.database.Reader(asn_dat_path, locales=self.getConfigurationValue('maxmind_locals'), mode=asn_mode)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not init %s. Exception: %s, Error: %s. " % (self.__class__.__name__, etype, evalue))

    def handleEvent(self, event):
        for lookup_field_name in self.source_fields:
            try:
                lookup_field_name_value = event[lookup_field_name]
            except KeyError:
                continue
            if not lookup_field_name_value or lookup_field_name_value == "-":
                continue
            maxmind_info_fields = None
            if isinstance(lookup_field_name_value, list):
                for field_value in lookup_field_name_value:
                    maxmind_info_fields = self.getGeoIpInfo(field_value)
                    maxmind_info_fields.update(self.getASNInfo(field_value))
                    if maxmind_info_fields:
                        break
            else:
                maxmind_info_fields = self.getGeoIpInfo(lookup_field_name_value)
                maxmind_info_fields.update(self.getASNInfo(lookup_field_name_value))
            if maxmind_info_fields:
                if self.target_field:
                    event[self.target_field] = maxmind_info_fields
                else:
                    event.update(maxmind_info_fields)
                break
        yield event

    @memoize(maxlen=1000)
    def getGeoIpInfo(self, hostname_or_ip):
        if not self.is_valid_ipv4_address(hostname_or_ip) and not self.is_valid_ipv6_address(hostname_or_ip):
            return {}
        try:
            geoip_result = self.geoip_db.city(hostname_or_ip)
        except geoip2.errors.AddressNotFoundError:
            return {}
        result_info_fields = {'city': geoip_result.city.name,
                              'postal_code': geoip_result.postal.code,
                              'country_name': geoip_result.country.name,
                              'country_code': geoip_result.country.iso_code,
                              'continent_code': geoip_result.continent.code,
                              'continent': geoip_result.continent.name,
                              'area_code': geoip_result.subdivisions.most_specific.iso_code,
                              'region_name': geoip_result.subdivisions.most_specific.name,
                              'longitude': geoip_result.location.longitude,
                              'latitude': geoip_result.location.latitude,
                              # Kibana’s ‘bettermap’ panel needs an array of floats in order to plot events on map.
                              'longlat': [geoip_result.location.longitude, geoip_result.location.latitude],
                              'time_zone': geoip_result.location.time_zone,
                              'metro_code': geoip_result.location.metro_code}

        if not self.maxmind_info_fields:
            return result_info_fields
        configured_geo_info_fields = {}
        for field_name in self.maxmind_info_fields:
            try:
                configured_geo_info_fields[field_name] = result_info_fields[field_name]
            except:
                pass
        return configured_geo_info_fields

    @memoize(maxlen=1000)
    def getASNInfo(self, hostname_or_ip):
        if not self.is_valid_ipv4_address(hostname_or_ip) and not self.is_valid_ipv6_address(hostname_or_ip):
            return {}
        try:
            asn_result = self.asn_db.asn(hostname_or_ip)
        except geoip2.errors.AddressNotFoundError:
            return {}
        result_info_fields = {'autonomous_system_number': asn_result.autonomous_system_number,
                              'autonomous_system_organization': asn_result.autonomous_system_organization}
        if not self.maxmind_info_fields:
            return result_info_fields
        configured_asn_info_fields = {}
        for field_name in self.maxmind_info_fields:
            try:
                configured_asn_info_fields[field_name] = result_info_fields[field_name]
            except:
                pass
        return configured_asn_info_fields

    def is_valid_ipv4_address(self, address):
        try:
            addr = socket.inet_pton(socket.AF_INET, address)
        except AttributeError:
            try:
                addr = socket.inet_aton(address)
            except socket.error:
                return False
            return address.count('.') == 3
        except socket.error:
            return False
        return True

    def is_valid_ipv6_address(self, address):
        try:
            addr = socket.inet_pton(socket.AF_INET6, address)
        except socket.error:
            return False
        return True
