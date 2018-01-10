#!/usr/bin/env python
# coding: utf-8

import os, sys, json, urllib2

def haCall(cmd):
    url = 'http://xxxx:8123/api/' + cmd
    #headers = {'x-ha-access': '', 'content-type': 'application/json'}
    return json.loads(urllib2.urlopen(url).read())

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

def validateToken(request):
    return request.has_key('accessToken') and request['accessToken'] == '25ec6cb46565638b1d3f58c3230ce99742a23622'

def getPropertyName(entity_id, attributes, state):
    if attributes.has_key('hageinie_property_name'):
        return attributes['hageinie_property_name']

    if state == 'on' or state == 'off':
        return 'powerstate'

    homebridge_sensor_type = attributes['homebridge_sensor_type'] if attributes.has_key('homebridge_sensor_type') else ''
    unit_of_measurement = attributes['unit_of_measurement'] if attributes.has_key('unit_of_measurement') else ''

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

        device['actions'] = ["Query"] #TODO

        devices.append(device)
    return {'devices': devices}

def controlDevice(name, request):
    return errorResponse('IOT_DEVICE_OFFLINE')

def queryDevice(name, request):
    return errorResponse('IOT_DEVICE_OFFLINE')

def handleRequest(header, request):
    name = header['name']
    if validateToken(request):
        namespace = header['namespace']
        if namespace == 'AliGenie.Iot.Device.Discovery':
            response = discoveryDevice()
        elif namespace == 'AliGenie.Iot.Device.Control':
            response = controlDevice(name, request)
        elif namespace == 'AliGenie.Iot.Device.Query':
            response = queryDevice(name, request)
        else:
            response = errorResponse('SERVICE_ERROR')
    else:
        response = errorResponse('ACCESS_TOKEN_INVALIDATE')

    # Check error and fill response name
    header['name'] = ('Error' if response.has_key('errorCode') else name) + 'Response'

    # Fill response deviceId
    if request.has_key('deviceId'):
        response['deviceId'] = request['deviceId']

    return response

print 'Content-Type: application/json'
print ''

#
try:
    if os.environ.has_key('REQUEST_METHOD') and os.environ['REQUEST_METHOD'] == 'POST':
        _request = json.load(sys.stdin)
        #print _request
    else:
        _request = {
            'header':{'namespace': 'AliGenie.Iot.Device.Discovery', 'name': 'DiscoveryDevices', 'payloadVersion':1},
            'payload':{'accessToken':'25ec6cb46565638b1d3f58c3230ce99742a23622'}
            }
    _header = _request['header']
    _response = handleRequest(_header, _request['payload'])
except:
    type, value, tb = sys.exc_info()
    import traceback
    print "".join(traceback.format_tb(tb))
    del tb
    _header = {'name': 'ErrorResponse'}
    _response = errorResponse('SERVICE_ERROR', 'service exception')

print json.dumps({"header": _header, "payload": _response}, indent=4, sort_keys=True)#, ensure_ascii=False)
