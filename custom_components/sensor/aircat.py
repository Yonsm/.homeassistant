#!/usr/bin/env python
#encoding:utf8

'''
YAML Example:
sensors:
  - platform: aircat
    #name: AirCat
    username: 139********
    password: ********
    #sensors: 1
    #scan_interval: 60
    monitored_conditions: # Optional
      - temperature
      - humidity
      - pm25
      - pm10
      - hcho
'''

import logging, os
import requests, json

# Const
TOKEN_PATH = '.aircat.token'
AUTH_CODE = 'feixun.SH_1'
USER_AGENT = 'zhilian/5.7.0 (iPhone; iOS 10.0.2; Scale/3.00)'
#AUTH_CODE = 'feixun*123.SH_7316142'
#USER_AGENT = 'ICode7Phone/3.0.0 (iPhone; iOS 11.2.2; Scale/2.00)'
LOGGER = logging.getLogger(__name__)

# Get homeassistant configuration path to store token
TOKEN_PATH = os.path.split(os.path.split(os.path.split(os.path.realpath(__file__))[0])[0])[0] + '/' + TOKEN_PATH

class AirCatData():
    def __init__(self, username, password):
        self._devs = None
        self._username = username
        self._password = password
        try:
            with open(TOKEN_PATH) as f:
                self._token = f.read()
                LOGGER.debug('load: path=%s, token=%s', TOKEN_PATH, self._token)
        except:
            self._token = None
            pass

    def update(self):
        try:
            result = self.fetch()
            if ('error' in result) and (result['error'] != '0'):
                LOGGER.debug('resetToken: error=%s', result['error'])
                self._token = None
                result = self.fetch()
            self._devs = result['data']['devs']
            LOGGER.debug('getIndexData: devs=%s', self._devs)
        except:
            import traceback
            LOGGER.error('exception: %s', traceback.format_exc())

    def fetch(self):
        if self._token == None:
            import hashlib
            md5 = hashlib.md5()
            md5.update(self._password.encode("utf8"))
            headers = {'User-Agent': USER_AGENT}
            data = {'authorizationcode': AUTH_CODE, 'password':md5.hexdigest().upper(), 'phonenumber': self._username}
            result = requests.post('https://accountsym.phicomm.com/v1/login', headers=headers, data=data).json()
            LOGGER.debug('getToken: result=%s', result)
            if 'access_token' in result:
                self._token = result['access_token']
                with open(TOKEN_PATH, 'w') as f:
                    f.write(self._token)
            else:
                return None
        headers = {'User-Agent': USER_AGENT, 'Authorization': self._token}
        return requests.get('https://aircleaner.phicomm.com/aircleaner/getIndexData', headers=headers).json()

if __name__ == '__main__':
    # For local call
    import sys
    LOGGER.addHandler(logging.StreamHandler(sys.stderr))
    LOGGER.setLevel(logging.DEBUG)
    if len(sys.argv) != 3:
        print('Usage: %s <username> <password>' % sys.argv[0])
        exit(0)
    data = AirCatData(sys.argv[1], sys.argv[2])
    data.update()
    print(data._devs)
    exit(0)

# Import homeassistant
from homeassistant.helpers.entity import Entity
from homeassistant.const import (CONF_NAME, CONF_USERNAME, CONF_PASSWORD, CONF_SENSORS, CONF_MONITORED_CONDITIONS)
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from datetime import timedelta
SCAN_INTERVAL = timedelta(seconds=60)

SENSOR_TYPES = {
    'pm25': ('pm25', 'μg/m³', 'blur'),
    'hcho': ('hcho', 'mg/m³', 'biohazard'),
    'temperature': ('temperature', '℃', 'thermometer'),
    'humidity': ('humidity', '%', 'water-percent')
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default='AirCat'): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_SENSORS, default=1): cv.positive_int,
    vol.Optional(CONF_MONITORED_CONDITIONS, default=['pm25', 'hcho', 'temperature', 'humidity']): vol.All(cv.ensure_list, vol.Length(min=1), [vol.In(SENSOR_TYPES)]),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    name = config.get(CONF_NAME)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    sensors = config.get(CONF_SENSORS)
    monitored_conditions = config[CONF_MONITORED_CONDITIONS]

    LOGGER.debug('setup_platform: name=%s, username=%s, password=%s, sensors=%d', name, username, password, sensors)

    AirCatSensor._data = AirCatData(username, password)
    AirCatSensor._update_index = 0
    AirCatSensor._conditions_count = len(monitored_conditions)

    i = 0
    devices = []
    while i < sensors:
        for type in monitored_conditions:
            devices.append(AirCatSensor(name, i, type))
        i += 1
    add_devices(devices, True)

class AirCatSensor(Entity):

    def __init__(self, name, index, type):
        tname,unit,icon = SENSOR_TYPES[type]
        if index:
            name += str(index + 1)        
        self._name = name + ' ' + tname
        self._index = index
        self._type = type
        self._unit = unit
        self._icon = 'mdi:' + icon

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def unit_of_measurement(self):
        return self._unit

    @property
    def available(self):
        attributes = self.attributes
        return attributes and attributes['online'] == '1'

    @property
    def state(self):
        attributes = self.attributes
        return attributes[self._type] if attributes else None

    @property
    def state_attributes(self):
        return self.attributes if self._type == 'pm25' else None

    @property
    def attributes(self):
        if AirCatSensor._data._devs and self._index < len(AirCatSensor._data._devs):
            return AirCatSensor._data._devs[self._index]['catDev']
        return None

    def update(self):
        LOGGER.debug('update: name=%s', self._name)
        if AirCatSensor._update_index % AirCatSensor._conditions_count == 0:
            AirCatSensor._data.update()
        AirCatSensor._update_index += 1
        LOGGER.info('End update: name=%s', self._name)
