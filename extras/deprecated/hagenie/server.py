#!/usr/bin/env python
# coding: utf-8


try:
    from BaseHTTPServer import HTTPServer
    from CGIHTTPServer import CGIHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer, CGIHTTPRequestHandler

import os, sys, ssl
import cgi, json
from stat import *

def _url_collapse_path_split(path):
    path_parts = []
    for part in path.split('/'):
        if part == '.':
            path_parts.append('')
        else:
            path_parts.append(part)
    # Filter out blank non trailing parts before consuming the '..'.
    path_parts = [part for part in path_parts[:-1] if part] + path_parts[-1:]
    if path_parts:
        tail_part = path_parts.pop()
    else:
        tail_part = ''
    head_parts = []
    for part in path_parts:
        if part == '..':
            head_parts.pop()
        else:
            head_parts.append(part)
    if tail_part and tail_part == '..':
        head_parts.pop()
        tail_part = ''
    return ('/' + '/'.join(head_parts), tail_part)

class ServerHandler(CGIHTTPRequestHandler):

    def do_POST(self):
        if self.is_cgi():
            self.run_cgi()
        else:
            self.send_error(501, "is_cgi:NO");
            self.do_GET()

    have_fork = False
    #cgi_directories = ['/']
    def is_cgi(self):
        self.cgi_info = _url_collapse_path_split(self.path)
        return True
        #is_cgi = CGIHTTPRequestHandler.is_cgi(self)
        #if is_cgi == True:
        #    pathname = '.' + self.path.split("?")[0]
        #    is_cgi = os.path.isfile(pathname) and self.is_executable(pathname)
        #return is_cgi

server = HTTPServer(('', 8122), ServerHandler)
certfile = os.path.dirname(sys.argv[0]) + '/server.pem'
if os.path.isfile(certfile):
    server.socket = ssl.wrap_socket (server.socket, certfile=certfile, server_side=True)
server.serve_forever()
