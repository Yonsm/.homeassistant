#!/usr/bin/env python

import os, sys

# Log HTTP request
REQUEST_METHOD = os.getenv('REQUEST_METHOD')
if REQUEST_METHOD:
	sys.stderr.write(REQUEST_METHOD + ' ' + os.environ['REQUEST_URI'])
	if REQUEST_METHOD == 'POST':
		sys.stderr.write('\n' + sys.stdin.read())

# Print content
print('Content-Type: text/json\r\n')
print("""{
  "access_token": "25ec6cb46565638b1d3f58c3230ce99742a23622",
  "expires_in": 3600,
  "token_type": "Bearer",
  "scope": null,
  "refresh_token": "a9f97c43a88c2f2c8270c53d4f1f2d5abc626e62"
}""")
