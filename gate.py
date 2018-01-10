#!/usr/bin/env python
# coding: utf-8

import json
import urllib2

def haCall(cmd):
	url = 'http://xxxx:8123/api/' + cmd
	headers = {'x-ha-access': '', 'content-type': 'application/json'}
	return urllib2.urlopen(url).read()

def errorResponse(errorCode, messsage = None):
	messages = {
	'INVALIDATE_CONTROL_ORDER':	'invalidate control order',
	'SERVICE_ERROR': 'service error',
	'DEVICE_NOT_SUPPORT_FUNCTION': 'device not support',
	'INVALIDATE_PARAMS': 'invalidate params',
	'DEVICE_IS_NOT_EXIST': 'device is not exist',
	'IOT_DEVICE_OFFLINE': 'device is offline',
	'ACCESS_TOKEN_INVALIDATE': ' access_token is invalidate'
	}
	return {'errorCode': errorCode, 'message': messsage if messsage else messages[errorCode]}

def validateToken(request):
	return request.has_key('accessToken') and request['accessToken'] == '25ec6cb46565638b1d3f58c3230ce99742a23622'

def discoveryDevice(request):
	devices = []
	return {'devices': devices}

def controlDevice(request):
	return errorResponse('DEVICE_IS_NOT_EXIST')

def queryDevice(request):
	return errorResponse('DEVICE_IS_NOT_EXIST')

def handleRequest(header, request):
	if validateToken(request):
		namespace = header['namespace']
		if namespace == 'AliGenie.Iot.Device.Discovery':
			response = discoveryDevice(request)
		elif namespace == 'AliGenie.Iot.Device.Control':
			response = controlDevice(request)
		elif namespace == 'AliGenie.Iot.Device.Query':
			response = queryDevice(request)
		else:
			response = errorResponse('SERVICE_ERROR')
	else:
		response = errorResponse('ACCESS_TOKEN_INVALIDATE')

	# Check error and fill response name
	if response.has_key('errorCode'):
		header['name'] = 'ErrorResponse'
	else:
		header['name'] += 'Response'

	# Fill response deviceId
	if request.has_key('deviceId'):
		response['deviceId'] = request['deviceId']

	return response

#
#try:
if True:
	#json.load(sys.stdin)
	request = {'header':{'namespace': 'AliGenie.Iot.Device.Discovery', 'name': 'DiscoveryDevices', 'payloadVersion':1}, 'payload':{'accessToken':'25ec6cb46565638b1d3f58c3230ce99742a23622'}};
	header = request['header']
	response = handleRequest(header, request['payload'])
#except:
else:
	header = {'name': 'ErrorResponse'}
	response = errorResponse('SERVICE_ERROR', 'service exception')

print 'Content-Type: application/json'
print ''
print json.dumps({"header": header, "payload": response})
