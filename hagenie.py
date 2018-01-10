#!/usr/bin/python

import BaseHTTPServer, CGIHTTPServer
import os, sys, ssl
import cgi, json
from stat import *

class ServerHandler(CGIHTTPServer.CGIHTTPRequestHandler):

    def do_POST(self):
        if self.is_cgi():
            self.run_cgi()
        else:
            self.send_error(501, "is_cgi:NO");
            self.do_GET()

    have_fork = False
    cgi_directories = ['/']
    def is_cgi(self):
        is_cgi = CGIHTTPServer.CGIHTTPRequestHandler.is_cgi(self)
        if is_cgi == True:
            pathname = '.' + self.path.split("?")[0]
            is_cgi = os.path.isfile(pathname) and self.is_executable(pathname)
        return is_cgi

server = BaseHTTPServer.HTTPServer(('', 8122), ServerHandler)
certfile = os.path.dirname(sys.argv[0]) + '/server.pem'
if os.path.isfile(certfile):
    server.socket = ssl.wrap_socket (server.socket, certfile=certfile, server_side=True)
server.serve_forever()
