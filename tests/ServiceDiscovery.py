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
                return {'server': server, 'port': port}
    return None

def discover_elasticsearch():
    servers_to_try = ['localhost', 'elasticsearch']
    ports_to_try = [9200]
    s = socket.socket()
    for server in servers_to_try:
        for port in ports_to_try:
            if s.connect_ex((server, port)) == 0:
                return {'server': server, 'port': port}
    return None

def discover_mongodb():
    servers_to_try = ['localhost', 'mongodb']
    ports_to_try = [27017]
    s = socket.socket()
    for server in servers_to_try:
        for port in ports_to_try:
            if s.connect_ex((server, port)) == 0:
                return {'server': server, 'port': port}
    return None


def getFreeTcpPortoOnLocalhost():
    # Get a free random port.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', 0))
    sock.listen(socket.SOMAXCONN)
    ipaddr, port = sock.getsockname()
    return (ipaddr, port)