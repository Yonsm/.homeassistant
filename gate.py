#!/usr/bin/env python
# coding: utf-8

import os, sys, json
import requests

# Log HTTP payload
REQUEST_METHOD = os.getenv('REQUEST_METHOD')
if REQUEST_METHOD:
	sys.stderr.write(REQUEST_METHOD + ' ' + os.environ['REQUEST_URI'])
	#if payload_METHOD == 'POST':
	#	sys.stderr.write('\n' + sys.stdin.read())

_accessToken = None
def validateToken(payload):
    #return 'accessToken' in payload and payload['accessToken'] == '25ec6cb46565638b1d3f58c3230ce99742a23622'
    if 'accessToken' in payload:
        global _accessToken
        _accessToken = payload['accessToken']
        return _accessToken.startswith('http')
    return False

def haCall(cmd, params=None):
    index = _accessToken.find('?')
    if index == -1:
        client_id = _accessToken
        client_scret = None
        headers = None
    else:
        client_id = _accessToken[:index]
        client_scret = _accessToken[index+1:]
        headers = {'x-ha-access': client_scret}
    url = client_id + '/api/' + cmd
    method = 'POST' if params else 'GET'
    sys.stderr.write('HA ' + method + ' ' + url)
    if client_scret:
        sys.stderr.write('?api_password=' + client_scret)
    if params:
        sys.stderr.write('\n' + json.dumps(params, indent=2))
    response = requests.request(method, url, params=params, headers=headers, verify=False)
    result = response.text
    sys.stderr.write('HA RESPONSE: ' + result)
    return json.loads(result)

def errorResponse(errorCode, messsage=None):
    messages = {
        'INVALIDATE_CONTROL_ORDER':    'invalidate control order',
        'SERVICE_ERROR': 'service error',
        'DEVICE_NOT_SUPPORT_FUNCTION': 'device not support',
        'INVALIDATE_PARAMS': 'invalidate params',
        'DEVICE_IS_NOT_EXIST': 'device is not exist',
        'IOT_DEVICE_OFFLINE': 'device is offline',
        'ACCESS_TOKEN_INVALIDATE': ' access_token is invalidate'
    }
    return {'errorCode': errorCode, 'message': messsage if messsage else messages[errorCode]}

def getPropertyName(entity_id, attributes, state):
    if 'hageinie_property_name' in attributes:
        return attributes['hageinie_property_name']

    if state == 'on' or state == 'off':
        return 'powerstate'

    homebridge_sensor_type = attributes['homebridge_sensor_type'] if 'homebridge_sensor_type' in attributes else ''
    unit_of_measurement = attributes['unit_of_measurement'] if 'unit_of_measurement' in attributes else ''

    #if :
    #    return 'color'
    if unit_of_measurement == u'°C' or unit_of_measurement == u'℃':
        return 'temperature'
    #if :
    #    return 'windspeed'
    #if :
    #    return 'brightness'
    #if :
    #    return 'fog'
    if ('humidity' in entity_id) or (homebridge_sensor_type == 'humidity'):
        return 'humidity'
    if ('pm25' in entity_id) or (homebridge_sensor_type == 'air_qulity'):
        return 'pm2.5'
    #if :
    #    return 'channel'
    #if :
    #    return 'number'
    #if :
    #    return 'direction'
    #if :
    #    return 'angle'
    #if :
    #    return 'anion'
    #if :
    #    return 'effluent'
    #if :
    #    return 'mode'
    #if :
    #    return 'lefttime'
    #if :
    #    return 'remotestatus'
    return None

def discoveryDevice():
    devices = []
    items = haCall('states')
    for item in items:
        device = {}
        attributes = item['attributes']
        entity_id = item['entity_id']
        device['deviceId'] = entity_id
        #https://open.bot.tmall.com/oauth/api/aliaslist
        device['deviceName'] = attributes['friendly_name']
        device['deviceType'] = item['entity_id'].split('.')[0]
        device['zone'] = '客厅' #TODO import from HA GROUP and https://open.bot.tmall.com/oauth/api/placelist
        device['brand'] = 'HomeAssistant'
        device['model'] = device['deviceType'] #TODO
        device['icon'] = 'https://home-assistant.io/demo/favicon-192x192.png'

        state = item['state']
        name = getPropertyName(entity_id, attributes, state)
        device['properties'] = [{'name': name, 'value': state}] if name else []

        device['actions'] = [
            'TurnOn',
            'TurnOff',
            'Query'
            ] #TODO

        devices.append(device)
    return {'devices': devices}

def getControlService(action):
    i = 0
    service = ''
    for c in action:
        service += (('_' if i else '') + c.lower()) if c.isupper() else c
        i += 1
    return service;

def controlDevice(name, payload):
    domain = payload['deviceType']
    service = getControlService(name)
    entity_id = payload['deviceId']
    params = {'entity_id': entity_id}
    items = haCall('services/' + domain + '/' + service, params)
    for item in items:
        if item['entity_id'] == entity_id:
            return {}
    return errorResponse('IOT_DEVICE_OFFLINE')

def queryDevice(name, payload):
    return errorResponse('IOT_DEVICE_OFFLINE')

def handleRequest(header, payload):
    name = header['name']
    if validateToken(payload):
        namespace = header['namespace']
        if namespace == 'AliGenie.Iot.Device.Discovery':
            response = discoveryDevice()
        elif namespace == 'AliGenie.Iot.Device.Control':
            response = controlDevice(name, payload)
        elif namespace == 'AliGenie.Iot.Device.Query':
            response = queryDevice(name, payload)
        else:
            response = errorResponse('SERVICE_ERROR')
    else:
        response = errorResponse('ACCESS_TOKEN_INVALIDATE')

    # Check error and fill response name
    header['name'] = ('Error' if 'errorCode' in response else name) + 'Response'

    # Fill response deviceId
    if 'deviceId' in payload:
        response['deviceId'] = payload['deviceId']

    return response

# Main process
try:
    if REQUEST_METHOD == 'POST':
        _payload = json.load(sys.stdin)
        sys.stderr.write('\n' + json.dumps(_payload, indent=2))
    else:
        # TEST only
        _payload = {
            #'header':{'namespace': 'AliGenie.Iot.Device.Discovery', 'name': 'DiscoveryDevices', 'payloadVersion':1, 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
            #'payload':{'accessToken':'25ec6cb46565638b1d3f58c3230ce99742a23622'}
            'header':{'namespace': 'AliGenie.Iot.Device.Control', 'name': 'TurnOn', 'payloadVersion':1, 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
            'payload':{'accessToken':'https://x.xxx.com:8123?password', 'attribute': 'powerstate', 'value': 'on', 'deviceType': 'switch','deviceId': 'switch.outlet'}
            }
    _header = _payload['header']
    _response = handleRequest(_header, _payload['payload'])
except:
    import traceback
    sys.stderr.write(traceback.format_exc())
    _header = {'name': 'ErrorResponse'}
    _response = errorResponse('SERVICE_ERROR', 'service exception')

# Process final result
_result = json.dumps({'header': _header, 'payload': _response}, indent=2, sort_keys=True)
if REQUEST_METHOD:
    sys.stderr.write('RESPONSE ' + _result)

print('Content-Type: text/html\r\n')
print(_result)
