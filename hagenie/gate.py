#!/usr/bin/env python
# coding: utf-8

# http://doc-bot.tmall.com/docs/doc.htm?treeId=393&articleId=107674&docType=1

import os, sys, json
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen


#
def log(message):
    #pass
    sys.stderr.write(message + '\n')


# Log HTTP payload
REQUEST_METHOD = os.getenv('REQUEST_METHOD')
if REQUEST_METHOD:
    log(REQUEST_METHOD + ' ' + os.environ['SCRIPT_NAME'] + '?' + os.environ['QUERY_STRING'] + '\n')
    #if payload_METHOD == 'POST':
    #    log(sys.stdin.read())


_accessToken = None
_ignoreAlias = False
def validateToken(payload):
    #return 'accessToken' in payload and payload['accessToken'] == '25ec6cb46565638b1d3f58c3230ce99742a23622'
    if 'accessToken' in payload:
        global _accessToken
        global _ignoreAlias
        _accessToken = payload['accessToken']
        if _accessToken.startswith('http') and (not 'xx.' in _accessToken):
            parts = _accessToken.split(':')
            _ignoreAlias = parts[1][-1:].isupper()   # Trick
            if not parts[1].startswith('//'):
                _accessToken = parts[0] + '://' + parts[1] + ':' + parts[2]
                #log('Rebuild accessToken: ' + _accessToken)
            return True
    return False


def haCall(cmd, data=None):
    index = _accessToken.index('?')
    client_id = _accessToken[:index]
    client_scret = _accessToken[index+1:]
    url = client_id + '/api/' + cmd + '?api_password=' + client_scret
    method = 'POST' if data else 'GET'
    log('HA ' + method + ' ' + url)# + (('?api_password=' + client_scret) if client_scret else ''))
    if data:
        log(data)
    if url.startswith('https'): # We need extra requests lib for HTTPS POST
        import requests
        result = requests.request(method, url, data=data, verify=False, timeout=10).text
    else:
        result = urlopen(url, data=data, timeout=10).read()

    #log('HA RESPONSE: ' + result)
    return json.loads(result)


def errorResult(errorCode, messsage=None):
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


DEVICE_TYPES = [
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
    'fingerprintlock',#: '指纹锁'
    'telecontroller',#: '万能遥控器'
    'dishwasher',#: '洗碗机'
    'dehumidifier',#: '除湿机'
]

INCLUDE_DOMAINS = {
    'climate': 'aircondition',
    'fan': 'fan',
    'light': 'light',
    'media_player': 'television',
    'remote': 'telecontroller',
    'switch': 'switch',
    'vacuum': 'roboticvacuum',
    }

EXCLUDE_DOMAINS = [
    'automation',
    'binary_sensor',
    'device_tracker',
    'group',
    'sensor',
    'zone',
    ]

# http://doc-bot.tmall.com/docs/doc.htm?treeId=393&articleId=108271&docType=1
def guessDeviceType(entity_id, attributes):
    if 'hagenie_deviceType' in attributes:
        return attributes['hagenie_deviceType']

    # Exclude with domain
    domain = entity_id[:entity_id.find('.')]
    if domain in EXCLUDE_DOMAINS:
        return None

    # Guess from entity_id
    for deviceType in DEVICE_TYPES:
        if deviceType in entity_id:
            return deviceType

    # Map from domain
    return INCLUDE_DOMAINS[domain] if domain in INCLUDE_DOMAINS else None


# https://open.bot.tmall.com/oauth/api/aliaslist
def guessDeviceName(entity_id, attributes, places, aliases):
    if 'hagenie_deviceName' in attributes:
        return attributes['hagenie_deviceName']

    # Remove place prefix
    name = attributes['friendly_name']
    for place in places:
        if name.startswith(place):
            name = name[len(place):]
            break

    if aliases is None:
        return name

    # Name validation
    for alias in aliases:
        if name == alias['key'] or name in alias['value']:
        	return name

    return None


#
def groupsAttributes(items):
    groups_attributes = []
    for item in items:
        group_entity_id = item['entity_id']
        if group_entity_id.startswith('group.') and not group_entity_id.startswith('group.all_'):
            group_attributes = item['attributes']
            if 'entity_id' in group_attributes:
                groups_attributes.append(group_attributes)
    return groups_attributes


# https://open.bot.tmall.com/oauth/api/placelist
def guessZone(entity_id, attributes, places, groups_attributes):
    if 'hagenie_zone' in attributes:
        return attributes['hagenie_zone']

    # Guess with friendly_name prefix
    name = attributes['friendly_name']
    for place in places:
        if name.startswith(place):
            return place

    # Guess from HomeAssistant group
    for group_attributes in groups_attributes:
        for child_entity_id in group_attributes['entity_id']:
            if child_entity_id == entity_id:
                if 'hagenie_zone' in group_attributes:
                    return group_attributes['hagenie_zone']
                return group_attributes['friendly_name']

    return None


#
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


#
def guessActions(entity_id, services=None):
    '''type = entity_id[:entity_id.find('.')]
    gactions = [
        'TurnOn',
        'TurnOff',
        'SelectChannel',
        'AdjustUpChannel',
        'AdjustDownChannel',
        'AdjustUpVolume',
        'AdjustDownVolume',
        'SetVolume',
        'SetMute',
        'CancelMute',
        'Play',
        'Pause',
        'Continue',
        'Next',
        'Previous',
        'SetBrightness',
        'AdjustUpBrightness',
        'AdjustDownBrightness',
        'SetTemperature',
        'AdjustUpTemperature',
        'AdjustDownTemperature',
        'SetWindSpeed',
        'AdjustUpWindSpeed',
        'AdjustDownWindSpeed',
        'SetMode',
        'SetColor',
        'OpenFunction',
        'CloseFunction',
        'Query',
        'QueryColor',
        'QueryPowerState',
        'QueryTemperature',
        'QueryHumidity',
        'QueryWindSpeed',
        'QueryBrightness',
        'QueryFog',
        'QueryMode',
        'QueryPM25',
        'QueryDirection',
        'QueryAngle'
    ]'''
    #for service in services:
    #    if type == service['domain']:
    #        for action in service['services']:
    return ['TurnOn', 'TurnOff']#TODO


#
def discoveryDevice():

    items = haCall('states')
    #services = haCall('services')

    places = json.loads(urlopen('https://open.bot.tmall.com/oauth/api/placelist').read())['data']
    if not _ignoreAlias:
        aliases = json.loads(urlopen('https://open.bot.tmall.com/oauth/api/aliaslist').read())['data']
        aliases.append({'key': '电视', 'value': ['电视机']})
    else:
        aliases = None
        log('Ignore alias checking to speed up!')
    groups_ttributes = groupsAttributes(items)

    devices = []
    for item in items:
        attributes = item['attributes']

        if attributes.get('hidden'):
            continue

        friendly_name = attributes.get('friendly_name')
        if friendly_name is None:
            continue

        entity_id = item['entity_id']
        deviceType = guessDeviceType(entity_id, attributes)
        if deviceType is None:
            continue

        deviceName = guessDeviceName(entity_id, attributes, places, aliases)
        if deviceName is None:
            continue

        zone = guessZone(entity_id, attributes, places, groups_ttributes)
        if zone is None:
            continue

        devices.append({
            'deviceId': entity_id,
            'deviceName': deviceName,
            'deviceType': deviceType,
            'zone': zone,
            'model': friendly_name,
            'brand': 'HomeAssistant',
            'icon': 'https://home-assistant.io/demo/favicon-192x192.png',
            'properties': guessProperties(entity_id, attributes, item['state']),
            'actions': guessActions(entity_id)#, services)
            })

        if not REQUEST_METHOD:
            log(str(len(devices)) + '. ' + deviceType + ':' + zone + '/' + deviceName + ((' <= ' + friendly_name) if friendly_name != deviceName else ''))

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
    entity_id = payload['deviceId']
    service = getControlService(name)
    domain = entity_id[:entity_id.find('.')]
    data = '{"entity_id":"' + entity_id + '"}'
    items = haCall('services/' + domain + '/' + service, data)
    #for item in items:
    #    if item['entity_id'] == entity_id:
    #        return {}
    return {} if (type(items) is list) else errorResult('IOT_DEVICE_OFFLINE')


#
def queryDevice(name, payload):
    entity_id = payload['deviceId']
    item = haCall('states/' + entity_id)
    if type(item) is dict:
        return {'powerstate': item['state']} #TODO
    return errorResult('IOT_DEVICE_OFFLINE')


#
def handleRequest(request):
    header = request['header']
    payload = request['payload']
    properties = None
    name = header['name']
    if validateToken(payload):
        namespace = header['namespace']
        if namespace == 'AliGenie.Iot.Device.Discovery':
            result = discoveryDevice()
        elif namespace == 'AliGenie.Iot.Device.Control':
            result = controlDevice(name, payload)
        elif namespace == 'AliGenie.Iot.Device.Query':
            result = queryDevice(name, payload)
            if not 'errorCode' in result:
                properties = result
                result = {}
        else:
            result = errorResult('SERVICE_ERROR')
    else:
        result = errorResult('ACCESS_TOKEN_INVALIDATE')

    # Check error and fill response name
    header['name'] = ('Error' if 'errorCode' in result else name) + 'Response'

    # Fill response deviceId
    if 'deviceId' in payload:
        result['deviceId'] = payload['deviceId']

    response = {'header': header, 'payload': result}
    if properties:
        response['properties'] = properties
    return response


# Main process
try:
    if REQUEST_METHOD == 'POST':
        _request = json.load(sys.stdin)
        log(json.dumps(_request, indent=2))
    else:
        # TEST only
        _request = {
            'header':{'namespace': 'AliGenie.Iot.Device.Discovery', 'name': 'DiscoveryDevices', 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
            #'header':{'namespace': 'AliGenie.Iot.Device.Control', 'name': 'TurnOn', 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
            #'header':{'namespace': 'AliGenie.Iot.Device.Query', 'name': 'Query', 'messageId': 'd0c17289-55df-4c8c-955f-b735e9bdd305'},
            'payload':{'accessToken':'https://xxx.xxx.x.xxX:8123?password'}
            }
    _response = handleRequest(_request)
except:
    import traceback
    log(traceback.format_exc())
    _response = {'header': {'name': 'errorResult'}, 'payload': errorResult('SERVICE_ERROR', 'service exception')}

# Process final result
_result = json.dumps(_response, indent=2)
if REQUEST_METHOD:
    log('RESPONSE ' + _result)

    print('Content-Type: text/json\r\n')
    print(_result)
