#!/usr/bin/env python3
# coding: utf-8

import os, sys
from urllib import parse

print('Content-Type: text/html\r\n')

str = "HTTP_CLIENT_IP=%s\nHTTP_X_FORWARDED_FOR=%s\nREMOTE_ADDR=%s\n\n" % (os.getenv("HTTP_CLIENT_IP"), os.getenv("HTTP_X_FORWARDED_FOR"),  os.getenv("REMOTE_ADDR"))
sys.stderr.write(str)

qs = os.environ['QUERY_STRING']
if not qs:
    sn = os.environ['SCRIPT_NAME'].split('?')
    if len(sn) > 1:
        qs = sn[1]
form = parse.parse_qs(qs)

if 'HAPI' in form and 'redirect_uri' in form:
    url = form['redirect_uri'][0] + '&code=' + form['HAPI'][0] + '&state=' + form['state'][0]

    print("<html><head><meta charset='UTF-8' /><meta http-equiv='refresh' content='20;url=" + url + "' /></head><body>转跳中...</body></html>");
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
