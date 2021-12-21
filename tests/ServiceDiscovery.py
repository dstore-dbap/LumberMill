#!/usr/bin/env python
import sys
import socket

def discover_redis():
    servers_to_try = ['localhost', 'redis']
    ports_to_try = [6379]
    s = socket.socket()
    for server in servers_to_try:
        for port in ports_to_try:
            if s.connect_ex((server, port)) == 0:
                s.close()
                return {'server': server, 'port': port}
    s.close()
    return None

def discover_elasticsearch():
    servers_to_try = ['localhost', 'elasticsearch']
    ports_to_try = [9200]
    s = socket.socket()
    for server in servers_to_try:
        for port in ports_to_try:
            if s.connect_ex((server, port)) == 0:
                s.close()
                return {'server': server, 'port': port}
    s.close()
    return None

def discover_mongodb():
    servers_to_try = ['localhost', 'mongodb']
    ports_to_try = [27017]
    s = socket.socket()
    for server in servers_to_try:
        for port in ports_to_try:
            if s.connect_ex((server, port)) == 0:
                s.close()
                return {'server': server, 'port': port}
    s.close()
    return None


def getFreeTcpPortoOnLocalhost():
    # Get a free random port.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', 0))
    s.listen(socket.SOMAXCONN)
    ipaddr, port = s.getsockname()
    s.close()
    return (ipaddr, port)