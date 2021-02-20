#!/usr/bin/env python
# coding: utf-8

import BaseHTTPServer, SimpleHTTPServer
import os, sys, ssl

httpd = BaseHTTPServer.HTTPServer(('', 8122), SimpleHTTPServer.SimpleHTTPRequestHandler)
certfile = os.path.dirname(sys.argv[0]) + '/server.pem'
if os.path.isfile(certfile):
    httpd.socket = ssl.wrap_socket (httpd.socket, certfile=certfile, server_side=True)
httpd.serve_forever()
