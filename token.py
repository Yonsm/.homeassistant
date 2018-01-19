#!/usr/bin/env python
# coding: utf-8

import os, sys, cgi

# Log HTTP request
REQUEST_METHOD = os.getenv('REQUEST_METHOD')
#if REQUEST_METHOD:
try:
  sys.stderr.write(REQUEST_METHOD + ' ' + os.environ['SCRIPT_NAME'] + '?' + os.environ['QUERY_STRING'] + '\n')
  #if REQUEST_METHOD == 'POST':
  #  sys.stderr.write(sys.stdin.read() + '\n')
  form = cgi.FieldStorage()
  for key in form.keys():
    sys.stderr.write(key + '=' + form[key].value + '\n')
  access_token = form['client_id'].value + '?' + form['client_secret'].value # Trick: Use access_token to pass client_id and client_secret
except:
  access_token = 'https://192.168.1.10:8123?password'

# Print content
print('Content-Type: text/json\r\n')
print('{\
"access_token": "' + access_token + '",\
"expires_in": 3600,\
"token_type": "Bearer",\
"scope": null,\
"refresh_token": "a9f97c43a88c2f2c8270c53d4f1f2d5abc626e62"\
}')
