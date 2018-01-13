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
    sys.stderr.write('\nHA ' + method + ' ' + url)
    if client_scret:
        sys.stderr.write('?api_password=' + client_scret)
    if params:
        sys.stderr.write('\n' + json.dumps(params, indent=2))
    response = requests.request(method, url, params=params, headers=headers, verify=False)
    result = json.loads(response.text)
    sys.stderr.write('HA RESPONSE: ' + json.dumps(result, indent=2))
    return result

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

def guessProperties(entity_id, attributes, state):
    unit = attributes['unit_of_measurement'] if 'unit_of_measurement' in attributes else ''
    if 'hagenie_propertyName' in attributes:
        name = attributes['attributes']
    elif state == 'on' or state == 'off':
        name = 'powerstate'
    #elif :
    #    name = 'color'
    elif unit == u'°C' or unit == u'℃':
        name = 'temperature'
    #elif :
    #    name = 'windspeed'
    #elif :
    #    name = 'brightness'
    #elif :
    #    name = 'fog'
    elif ('hum' in entity_id) and (unit == '%'):
        name = 'humidity'
    elif ('pm25' in entity_id) and (unit == 'ug/m3'):
        name = 'pm2.5'
    #elif :
    #    name = 'channel'
    #elif :
    #    name = 'number'
    #elif :
    #    name = 'direction'
    #elif :
    #    name = 'angle'
    #elif :
    #    name = 'anion'
    #elif :
    #    name = 'effluent'
    #elif :
    #    name = 'mode'
    #elif :
    #    name = 'lefttime'
    #elif :
    #    name = 'remotestatus'
    else:
        return []
    return [{'name': name, 'value': state}]

def guessDeviceType(entity_id):
    deviceTypes = {
        'television',#: '电视',
        'light',#: '灯',
        'aircondition',#: '空调',
        'airpurifier',#: '空气净化器',
        'outlet',#: '插座',
        'switch',#: '开关',
        'roboticvacuum',#: '扫地机器人',
        'curtain',#: '窗帘',
        'humidifier',#: '加湿器',
        'fan',#: '风扇',
        'bottlewarmer',#: '暖奶器',
        'soymilkmaker',#: '豆浆机',
        'kettle',#: '电热水壶',
        'watercooler',#: '饮水机',
        'cooker',#: '电饭煲',
        'waterheater',#: '热水器',
        'oven',#: '烤箱',
        'waterpurifier',#: '净水器',
        'fridge',#: '冰箱',
        'STB',#: '机顶盒',
        'sensor',#: '传感器',
        'washmachine',#: '洗衣机',
        'smartbed',#: '智能床',
        'aromamachine',#: '香薰机',
        'window',#: '窗',
        'kitchenventilator',#: '抽油烟机',
        'fingerprintlock'#: '指纹锁'
    }
    for deviceType in deviceTypes:
        if deviceType in entity_id:
            return deviceType

    type = entity_id[10:-1] if entity_id.startswith('group.all_') else entity_id[:entity_id.find('.')]
    #if type == 'switch':
    #    return outlet if 'outlet' in entity_id else type
    #elif type in ['sensor', 'light', 'fan']:
    #    return type
    if type == 'media_player':
        return 'television'
    elif type == 'vacuum':
        return 'roboticvacuum'
    return None

# https://open.bot.tmall.com/oauth/api/aliaslist
def guessDeviceName(entity_id, attributes):
    if 'hagenie_deviceName' in attributes:
        return attributes['hagenie_deviceName']
    return attributes['friendly_name']

# https://open.bot.tmall.com/oauth/api/placelist
def guessZone(entity_id, attributes):
    return '客厅' #TODO import from HA GROUP and

#
def discoveryDevice():
    devices = []
    items = haCall('states')
    for item in items:
        entity_id = item['entity_id']
        deviceType = guessDeviceType(entity_id)
        if deviceType == None:
            continue
        attributes = item['attributes']
        device = {}
        device['deviceId'] = entity_id
        device['deviceName'] = guessDeviceName(entity_id, attributes)
        device['deviceType'] = deviceType
        device['zone'] = guessZone(entity_id, attributes)
        device['brand'] = 'HomeAssistant'
        device['model'] = attributes['friendly_name']
        device['icon'] = 'https://home-assistant.io/demo/favicon-192x192.png'
        device['properties'] = guessProperties(entity_id, attributes, item['state'])

        device['actions'] = [
            'TurnOn',
            'TurnOff',
            'Query'
            ] #TODO

        devices.append(device)
    return {'devices': devices}

#
def getControlService(action):
    i = 0
    service = ''
    for c in action:
        service += (('_' if i else '') + c.lower()) if c.isupper() else c
        i += 1
    return service;

#
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

#
def queryDevice(name, payload):
    return errorResponse('IOT_DEVICE_OFFLINE')

#
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
            'header':{'namespace': 'AliGenie.Iot.Device.Discovery', 'name': 'DiscoveryDevices', 'payloadVersion':1, 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
            'payload':{'accessToken':'https://xxx.xxx.net:8123?password'}
            #'header':{'namespace': 'AliGenie.Iot.Device.Control', 'name': 'TurnOn', 'payloadVersion':1, 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
            #'payload':{'accessToken':'https://xxx.xxx.net:8123?password', 'attribute': 'powerstate', 'value': 'on', 'deviceType': 'switch','deviceId': 'switch.outlet'}
            }
    _header = _payload['header']
    _response = handleRequest(_header, _payload['payload'])
except:
    import traceback
    sys.stderr.write(traceback.format_exc())
    _header = {'name': 'ErrorResponse'}
    _response = errorResponse('SERVICE_ERROR', 'service exception')

# Process final result
_result = json.dumps({'header': _header, 'payload': _response}, indent=2)
if REQUEST_METHOD:
    sys.stderr.write('\nRESPONSE ' + _result)

print('Content-Type: text/html\r\n')
print(_result)
