#!/usr/bin/env python
#
#  tcp_socket_throughput.py
#  TCP Socket Connection Throughput Tester
#  Corey Goldberg (www.goldb.org), 2008

import sys
import time
import socket
from ctypes import c_int, c_bool
from multiprocessing import Process, Value, Lock


host = sys.argv[1]
port = int(sys.argv[2]) if len(sys.argv) == 3 else 5151

process_count = 5  # concurrent sender agents

counter_lock = Lock()
def increment(counter):
    with counter_lock:
        counter.value += 1

def reset(counter):
    with counter_lock:
        counter.value = 0

class Controller:
    def __init__(self):
        self.count_ref = Value(c_int)
        self.alive = Value(c_bool)

    def start(self):
        self.alive = True
        for i in range(process_count):
            agent = Agent(self.count_ref, self.alive)
            agent.start()
        print 'started %d threads' % (i + 1)
        while self.alive:
            line = 'connects/sec: %s' % self.count_ref.value
            reset(self.count_ref)
            print chr(0x08) * len(line)
            print line
            time.sleep(1)

class Agent(Process):
    def __init__(self, count_ref, parent_alive):
        Process.__init__(self)
        self.daemon = True
        self.count_ref = count_ref
        self.parent_alive = parent_alive

    def run(self):
        start = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        alive = True
        while alive:
            if time.time() >= start + 20:
                self.parent_alive = alive = False
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((host, port))
                now = "%f" % time.time()
                #message = 'Jun 6 05:22:39 lb1 nginx: agora 1370496159.983 dbap-titus.dstore.de GET "/'+now+'/?Version=200812&AccessKeyID=E9GADFFDE467&Operation=GetItems&Bereich=Schuhe&Marke=%22Carhartt%22%2C%22Volcom%22%2C%22ES%22%2C%22Foundation%22%2C%22Converse-Skate%22%2C%22DC+Shoes%22&Template=FacetedBrowsing_Bereich_DE&XSLTs=StandardTransformation&Kundeninfo=%22Lieferbar%22%2C%22lieferbar%22%2C%22coming+soon%22&RowCount=80&Sort=Brandneu_DESC%2CDatum_DESC&Brandneu=1&Query=Binaries_vorderansicht%3A%5B0+TO+9999999999%5D" "" - 200 6460 741 0.158 172.31.255.39 53939 "-" "/de_DE/Schuhe/Carhartt,Volcom,ES,Foundation,Converse-Skate,DC+Shoes/new.html" "curl/7.15.5 libcurl/7.15.5 OpenSSL/0.9.8b zlib/1.2.3 server/www.titus.de" MISS "0.158" "172.31.255.128:8182" "application/xml; charset=UTF-8" "deflate, gzip" "gzip" ""'
                message ='192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/ HTTP/1.0" 200 3395'
                s.sendall('%s\n' % message)
                increment(self.count_ref)
                s.close()
                time.sleep(.0000001) #.0000001
            except:
                self.parent_alive = alive = False
                etype, evalue, etb = sys.exc_info()
                print 'Exception: %s, Error: %s.' % (etype, evalue)

if __name__ == '__main__':
    controller = Controller()
    controller.start()