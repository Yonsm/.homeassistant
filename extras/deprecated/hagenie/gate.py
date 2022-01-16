#!/usr/bin/env python3
# coding: utf-8

# http://doc-bot.tmall.com/docs/doc.htm?treeId=393&articleId=107674&docType=1

import os, sys, json
try:
    from urllib2 import urlopen
    reload(sys)
    sys.setdefaultencoding('utf8')
except ImportError:
    from urllib.request import urlopen

#
def log(message):
    pass
    sys.stderr.write(message + '\n')

str = "HTTP_CLIENT_IP=%s\nHTTP_X_FORWARDED_FOR=%s\nREMOTE_ADDR=%s\n\n" % (os.getenv("HTTP_CLIENT_IP"), os.getenv("HTTP_X_FORWARDED_FOR"),  os.getenv("REMOTE_ADDR"))
sys.stderr.write(str)


# Log HTTP payload
REQUEST_METHOD = os.getenv('REQUEST_METHOD')
if REQUEST_METHOD:
    log(REQUEST_METHOD + ' ' + os.environ['SCRIPT_NAME'] + '?' + os.environ['QUERY_STRING'] + '\n')
    #if payload_METHOD == 'POST':
    #    log(sys.stdin.read())


_haUrl = None
_accessToken = None
_checkAlias = False
def validateToken(payload):
    if 'accessToken' in payload:
        accessToken = payload['accessToken']
        if accessToken.startswith('http'):
            global _haUrl
            global _checkAlias
            global _accessToken
            parts = accessToken.split('_')
            _checkAlias = parts[1][-1:].isupper()   # Trick
            _haUrl = parts[0] + '://' + parts[1] + ':' + parts[2] + '/api/%s'
            _accessToken = parts[3]
            #log('HA URL: ' + _haUrl +  ', accessToken: ' + _accessToken)
            return True
    return False


def haCall(cmd, data=None):
    url = _haUrl % cmd
    method = 'POST' if data else 'GET'
    log('HA ' + method + ' ' + url)
    if data:
        log(data)

    headers = {'Authorization': 'Bearer ' + _accessToken, 'Content-Type': 'application/json'} if _accessToken else None

    if url.startswith('https') or headers: # We need extra requests lib for HTTPS POST
        import requests
        result = requests.request(method, url, data=data, headers=headers, timeout=3).text
    else:
        result = urlopen(url, data=data, timeout=3).read()

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
    'sensor': 'sensor',
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

    if aliases is None or entity_id.startswith('sensor'):
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
        if group_entity_id.startswith('group.') and not group_entity_id.startswith('group.all_') and group_entity_id != 'group.default_view':
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
def guessPropertyAndAction(entity_id, attributes, state):
    # http://doc-bot.tmall.com/docs/doc.htm?treeId=393&articleId=108264&docType=1
    # http://doc-bot.tmall.com/docs/doc.htm?treeId=393&articleId=108268&docType=1
    # Support On/Off/Query only at this time
    if 'hagenie_propertyName' in attributes:
        name = attributes['hagenie_propertyName']

    elif entity_id.startswith('sensor.'):
        unit = attributes['unit_of_measurement'] if 'unit_of_measurement' in attributes else ''
        if unit == u'°C' or unit == u'℃':
            name = 'Temperature'
        elif unit == 'lx' or unit == 'lm':
            name = 'Brightness'
        elif ('hcho' in entity_id):
            name = 'Fog'
        elif ('humidity' in entity_id):
            name = 'Humidity'
        elif ('pm25' in entity_id):
            name = 'PM2.5'
        elif ('co2' in entity_id):
            name = 'WindSpeed'
        else:
            return (None, None)
    else:
        name = 'PowerState'
        if state != 'off':
            state = 'on'
    return ({'name': name.lower(), 'value': state}, 'Query' + name)

#
def discoveryDevice():

    items = haCall('states')
    #services = haCall('services')

    places = json.loads(urlopen('https://open.bot.tmall.com/oauth/api/placelist').read())['data']
    if _checkAlias:
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

        prop,action = guessPropertyAndAction(entity_id, attributes, item['state'])
        if prop is None:
            continue

        # Merge all sensors into one for a zone
        # https://bbs.hassbian.com/thread-2982-1-1.html
        if deviceType == 'sensor':
            for sensor in devices:
                if sensor['deviceType'] == 'sensor' and zone == sensor['zone']:
                    deviceType = None
                    if not action in sensor['actions']:
                        sensor['properties'].append(prop)
                        sensor['actions'].append(action)
                        sensor['model'] += ' ' + friendly_name
                        # SHIT, length limition in deviceId: sensor['deviceId'] += '_' + entity_id
                    else:
                        log('SKIP: ' + entity_id)
                    break
            if deviceType is None:
                continue
            deviceName = '传感器'
            entity_id = zone

        devices.append({
            'deviceId': entity_id,
            'deviceName': deviceName,
            'deviceType': deviceType,
            'zone': zone,
            'model': friendly_name,
            'brand': 'HomeAssistant',
            'icon': 'https://home-assistant.io/demo/favicon-192x192.png',
            'properties': [prop],
            'actions': ['TurnOn', 'TurnOff', 'Query', action] if action == 'QueryPowerState' else ['Query', action]
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
    if domain == 'cover':
        service = 'close_cover' if service == 'turn_off' else 'open_cover'
    items = haCall('services/' + domain + '/' + service, data)
    #for item in items:
    #    if item['entity_id'] == entity_id:
    #        return {}
    return {} if (type(items) is list) else errorResult('IOT_DEVICE_OFFLINE')


#
def queryDevice(name, payload):
    deviceId = payload['deviceId']

    if payload['deviceType'] == 'sensor':
        items = haCall('states')

        entity_ids = None
        for item in items:
            attributes = item['attributes']
            if item['entity_id'].startswith('group.') and (attributes['friendly_name'] == deviceId or attributes.get('hagenie_zone') == deviceId):
                entity_ids = attributes.get('entity_id')
                break

        if entity_ids:
            properties = [{'name':'powerstate', 'value':'on'}]
            for item in items:
                entity_id = item['entity_id']
                attributes = item['attributes']
                if entity_id.startswith('sensor.') and (entity_id in entity_ids or attributes['friendly_name'].startswith(deviceId) or attributes.get('hagenie_zone') == deviceId):
                    prop,action = guessPropertyAndAction(entity_id, attributes, item['state'])
                    if prop is None:
                        continue
                    properties.append(prop)
            return properties
    else:
        item = haCall('states/' + deviceId)
        if type(item) is dict:
            return {'name':'powerstate', 'value':item['state']}
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
            'payload':{'accessToken':'https_192.168.1.10_8123_token'}
            }
    _response = handleRequest(_request)
except:
    import traceback
    log(traceback.format_exc())
    _response = {'header': {'name': 'errorResult'}, 'payload': errorResult('SERVICE_ERROR', 'service exception')}

# Process final result
_result = json.dumps(_response, indent=2, ensure_ascii=False)
if REQUEST_METHOD:
    log('RESPONSE ' + _result)

    print('Content-Type: application/json\r\n')
    print(_result)
