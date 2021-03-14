#!/usr/bin/env python
# coding: utf-8

import os, sys, cgi

print('Content-Type: text/json\r\n')

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
  #access_token = form['client_id'].value + '?' + form['client_secret'].value # Trick: Use access_token to pass client_id and client_secret
  access_token = form['code'].value if 'code' in form else form['refresh_token'].value
except:
  import traceback
  sys.stderr.write(traceback.format_exc())
  access_token = 'http_192.168.1.10_8123_password'

# Print content
print('{\
"access_token": "' + access_token + '",\
"expires_in": 3600,\
"token_type": "Bearer",\
"scope": null,\
"refresh_token": "' + access_token + '"\
}')
