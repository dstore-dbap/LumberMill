#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys
import os
import ConfigParser
import httplib
import socket
import StringIO
import logging
import xml.etree.ElementTree as ElementTree

class SolrStorageHandler:
    """
    StorageHandler to store SyslogMessages into a solr server.
    
    This is done via a http post request using the httplib. Some testing showed that pyes 
    seems to be more cpu intensive than httplib.
    """
    def __init__(self):
        # get our logging facility
        self.logger = logging.getLogger(self.__class__.__name__)
        self._readConfig()
        self.host = self.config.get("General","SOLR_HOST")
        self.url = self.config.get("General","SOLR_CATALOG_PATH")+'/update'
        self.commit_after_max_store_data_requests = self.config.get("General","COMMIT_AFTER_NUMBER_OF_STORE_DATA_CALLS")
        globals()["SolrDataStorageHandler_commit_counter"] = 0
        self.commit_counter = globals()["SolrDataStorageHandler_commit_counter"]

    def storeData(self, data):
        """Prepare the log data to be stored in solr index.
        
        Also maintain a counter for sending a commit message to solr. 
        This takes care that the data near time available to search clients.
        
        @type data: list of dictionaries
        @param data: list of parsed log messages
        """
        
        if len(data) == 0:
            return
        xml_document = self._dataToSolrXml(data)
        self._sendRequest(xml_document);
        self.commit_counter += 1
        if self.commit_counter > self.commit_after_max_store_data_requests:
            self._sendCommitRequest()

    def _readConfig(self):
        """
        Read and parse the configfile for the SyslogMessageScanner.
        
        It expects to find the config file in a subdir named conf.
        The file itself should be named messagescanner.conf 
        """
        # get the basepath
        pathname = os.path.abspath(sys.argv[0])
        self.config_pathname = pathname[:pathname.rfind("/")]+"/conf"
        try:
            self.config = ConfigParser.ConfigParser()
            self.config.readfp(open(self.config_pathname+"/solrstoragehandler.conf"))
        except Exception, ue:
            print >>sys.stderr, '%s:'%sys.argv[0], ue
            sys.exit(1)

    def _dataToSolrXml(self, data):
        """Format data to an xml document for solr
        
        @type data: list of dictionaries
        @param data: list of parsed log messages
        
        @rtype: string
        @returns: A string representing then data as xml document.
        """
        xml_document = "<add allowDups='true' commitWithin='2000'>\n"
        for datarow in self.data:
            xml_document += "<doc>\n"
            for fieldname, fieldvalue in datarow.iteritems():
                xml_document += "<field name='"+fieldname+"'><![CDATA["+str(fieldvalue)+"]]></field>\n"
            xml_document += "</doc>\n"
        xml_document += "</add>\n"
        if self.config.get("Debug", "xml_data") == "True":
            print "%s" % xml_document
        return xml_document      
    
    def _sendCommitRequest(self):
        """Create commit xml and send to solr"""
        self.commit_counter = 0
        xml_document = '<commit/>'
        self._sendRequest(xml_document);

    def _sendRequest(self, request_payload):
        socket.setdefaulttimeout(25)
        solrWebservice = httplib.HTTP(self.host)
        solrWebservice.putrequest("POST", self.url)
        solrWebservice.putheader("User-Agent", "Python post")
        solrWebservice.putheader("Content-type", "text/xml;") #charset=\"UTF-8\"
        solrWebservice.putheader("Content-length", "%d" % len(request_payload))
        try:
            solrWebservice.endheaders()
            self.logger.debug("Sending xml data to solr. Server: "+self.host+". URL: "+self.url);
            self.logger.debug("XML Document:"+request_payload);
            solrWebservice.send(request_payload)
        except Exception, e:
            try:
                self.logger.error("Solr cummunication error: "+e[1])
                self.logger.error(self.host+":"+self.url)
            except:
                self.logger.error("Solr cummunication error: "+str(e))
            return

        # get the response
        try:
            http_statuscode, statusmessage, header = solrWebservice.getreply()
            response_string = solrWebservice.getfile().read()
            self.logger.debug("Solr server said: HttpStatus: "+str(http_statuscode)+", Response: "+response_string);
        except Exception, e:
            try:
                self.logger.error("Solr cummunication error: "+e[1])
            except:
                self.logger.error("Solr cummunication error: "+str(e))
            return

        if(http_statuscode != 200):
            self.logger.error("Solr returncode: "+str(http_statuscode)+". Error: "+response_string+". XML Document:"+request_payload)
            return
        try:
            response = ElementTree.parse(StringIO.StringIO(response_string))
            for responseElement in response.getiterator("int"):
                if responseElement.get('name') == 'status':
                    response_status = int(responseElement.text)
                elif responseElement.get('name') == 'QTime':
                    query_time = int(responseElement.text)
            self.logger.debug("Solr query send. ResponseStatus: "+str(response_status)+", QueryTime): "+str(query_time));
        except Exception, e:
            self.logger.error("Could not parse solr response. Response was:"+response_string)
            self.logger.error("%s: %s" %(Exception, e))
