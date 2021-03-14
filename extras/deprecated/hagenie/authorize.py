#!/usr/bin/env python
# coding: utf-8

import os, sys, cgi

# Log HTTP request
REQUEST_METHOD = os.getenv('REQUEST_METHOD')
if REQUEST_METHOD:
    sys.stderr.write(REQUEST_METHOD + ' ' + os.environ['SCRIPT_NAME'] + '?' + os.environ['QUERY_STRING'] + '\n')

form = cgi.FieldStorage()
for key in form.keys():
    sys.stderr.write(key + '=' + form[key].value + '\n')

# Print content
print('Content-Type: text/html\r\n')

if 'HAPI' in form and 'redirect_uri' in form:
    url = form['redirect_uri'].value + '&code=' + form['HAPI'].value + '&state=' + form['state'].value
    print("<html><head><meta charset='UTF-8' /><meta http-equiv='refresh' content='1;url=" + url + "' /></head><body>转跳中...</body></html>");
    exit(0)

print("""<html>
<head><meta charset='UTF-8'></head>
<body>
    <font size='2'>欢迎使用 HAGenie - 天猫精灵 + HomeAssistant 网关<br><br></font>
    <form name='form'>
        <p>地址：<br>
        <input type='text' id='HURL' placeholder='http://xx.xx.xx:8123' size=50><font color=red>*</font>
        <p>密码：<br>
        <input type='password' id='HPWD' placeholder='无' size=50></p>
        <p><br>
        <input type='button' value=' 继 续 ' size=20 onclick='location.href += "&HAPI=" + document.getElementById("HURL").value.replace("://","_").replace(":","_") + "_" + document.getElementById("HPWD").value'>
    </form>
</body>
<html>""")
