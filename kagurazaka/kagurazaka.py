#!/usr/bin/env python3

import argparse
import http.server
import logging
import os
import re
import select
import socket
import sys
import threading

import gfwhosts


LOGGING_LEVEL = logging.INFO
USE_SOCKET = True

MAX_RX = 32768

__version__ = "v1.0.2"
kagurazaka_agent = "kagurazaka-agent/" + __version__

HTTP_VERSION = "HTTP/1.0"

use_proxy = False

def hosts(host):
    if host in gfwhosts.hosts_list:
        logging.info('%s -> %s' % (host, gfwhosts.hosts_list[host]))
        return gfwhosts.hosts_list[host]
    else:
        return host

def parse_header(header):
    # https://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html#sec5
    request_line_re = re.compile(br'''
        (\w*)\s                                 # method
        ((\w+://)?([^:/\s]+)(:(\d+))?(/.*)?)\s  # scheme://host:port/path
        (.+)                                    # http_version
        ''', re.VERBOSE)
    METHOD = 1
    REQUEST_URI = 2
    SCHEME = 3
    HOST = 4
    PORT = 6
    PATH = 7
    HTTP_VERSION = 8

    request_line = header.split(b'\r\n')[0]
    match = request_line_re.match(request_line)

    if match:
        group = match.group
        method = group(METHOD).decode()
        host = group(HOST).decode().lower()
        port = group(PORT)
        if port:
            port = int(port)
        else:
            port = 80

        return True, {'port':port, 'host':host, 'method':method}
    else:
        return False, {}



class KagurazakaThread(threading.Thread):
    def __init__(self, client_connection, client_address):
        threading.Thread.__init__(self)
        self.client_connection = client_connection
        self.client_address = client_address

    def bridge(self):
        while True:
            [rx, _, _] = select.select([self.client_connection, self.server_socket], [], [])

            if rx:
                if rx[0] == self.client_connection:
                    tx = self.server_socket
                else:
                    tx = self.client_connection
            else:
                return

            data = rx[0].recv(MAX_RX)

            if self.parsed_header['method'] != 'CONNECT' and data and rx[0] == self.client_connection:
                ret, parsed_header = parse_header(data)
                if ret:
                    if parsed_header['host'] != self.parsed_header['host'] or \
                            parsed_header['port'] != self.parsed_header['port'] or \
                            parsed_header['method'] != self.parsed_header['method']:
                        logging.debug('%s -> %s' % (self.parsed_header, parsed_header))
                        self.parsed_header = parsed_header
                        self.server_socket.close()

                        if self.parsed_header['method'] == 'CONNECT':
                            return


                        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        tx = self.server_socket

                        # host middle ware
                        self.parsed_header['host'] = hosts(self.parsed_header['host'])

                        if use_proxy:
                            pass
                        else:
                            self.server_socket.connect((self.parsed_header['host'], self.parsed_header['port']))
                else:
                    return

            if len(data):
                tx.send(data)
            else:
                return

    def run(self):
        # Just let the thread module handle exception
        try:
            self.run_raw()
        finally:
            logging.info('<< EXIT %s' % self.parsed_header)

            self.client_connection.close()
            if hasattr(self, 'server_socket'):
                self.server_socket.close()

    def run_raw(self):
        self.header = self.client_connection.recv(MAX_RX)
        logging.debug(self.header)

        ret, self.parsed_header = parse_header(self.header)
        if ret:
            logging.info('%s %s %s', self.parsed_header['method'], self.parsed_header['host'], self.parsed_header['port'])
        else:
            logging.warning('Request match fail, header: %s', self.header)
            return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # host middle ware
        self.parsed_header['host'] = hosts(self.parsed_header['host'])

        if use_proxy:
            pass
        else:
            self.server_socket.connect((self.parsed_header['host'], self.parsed_header['port']))
            if self.parsed_header['method'] == 'CONNECT':
                logging.debug('Use CONNECT')
                self.client_connection.send(("HTTP/1.1 200 Connection established\r\nProxy-agent: %s\r\n\r\n" % kagurazaka_agent).encode())
            else:
                self.server_socket.send(self.header)
            self.bridge()

def main_socket():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.bind(('', 8888))
    client_socket.listen(512)

    while True:
        client_connection, client_address = client_socket.accept()
        KagurazakaThread(client_connection, client_address).start()


if __name__ == "__main__":
    logging.basicConfig(level=LOGGING_LEVEL)

    if USE_SOCKET:
        main_socket()

''' Websites
I can't write any python program without Google, So below is a list
of the sites which I think is helpful when writing this tool.

Simple Web Proxy Python, by LUU GIA THUY, 2011
http://luugiathuy.com/2011/03/simple-web-proxy-python/

A database of open-source HTTP proxies written in python
http://proxies.xhaus.com/python/

Tiny HTTP Proxy in Python, by SUZUKI Hisao, 2006
http://www.oki-osk.jp/esc/python/proxy/

最新可用的google hosts文件
(Chinese, Most updated google hosts file)
https://github.com/racaljk/hosts

Hypertext Transfer Protocol -- HTTP/1.1
https://www.w3.org/Protocols/rfc2616/rfc2616.html
https://tools.ietf.org/html/rfc2616

Persistent Connection Behavior of Popular Browsers
http://pages.cs.wisc.edu/~cao/papers/persistent-connection.html

Guidelines for Web Content Transformation Proxies 1.0
https://www.w3.org/TR/ct-guidelines/
'''
