#!/usr/bin/env python

import os, sys

# Log HTTP request
REQUEST_METHOD = os.getenv('REQUEST_METHOD')
if REQUEST_METHOD:
	sys.stderr.write(REQUEST_METHOD + ' ' + os.environ['REQUEST_URI'])
	if REQUEST_METHOD == 'POST':
		sys.stderr.write('\n' + sys.stdin.read())

# Print content
print('Content-Type: text/html\r\n')
print("""<html>
<body>	
	<script>
		function getQueryString(name) {
		    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i");
		    var r = window.location.search.substr(1).match(reg);
		    if (r != null) return unescape(r[2]); return null;
		}  

		var url = getQueryString("redirect_uri") + "&code=4ad21b7fd08b9c91314190ef441e1fba5d6aa449" + "&state=" + getQueryString("state");
		document.write("Continue: <a href='" + url + "'>"  + url + "</a>");
	</script>
</body>
<html>""")
