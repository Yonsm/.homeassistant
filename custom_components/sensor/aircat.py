#!/usr/bin/env python
#encoding:utf8

import logging, os, time
import requests, json

# Const
DEFAULT_NAME = 'AirCat'
TOKEN_PATH = '.aircat.token'
AUTH_CODE = 'feixun.SH_1'
USER_AGENT = 'zhilian/5.7.0 (iPhone; iOS 10.0.2; Scale/3.00)'
#AUTH_CODE = 'feixun*123.SH_7316142'
#USER_AGENT = 'ICode7Phone/3.0.0 (iPhone; iOS 11.2.2; Scale/2.00)'
LOGGER = logging.getLogger(__name__)

# Get homeassistant configuration path to store token
#TOKEN_PATH = os.path.split(os.path.split(os.path.split(os.path.realpath(__file__))[0])[0])[0] + '/' + TOKEN_PATH

class AirCatData():
    def __init__(self, username, password, scan_interval=0):
        self._devs = None
        self._username = username
        self._password = password
        self._lastime = 0
        self._scan_interval = scan_interval
        try:
            with open(TOKEN_PATH) as f:
                self._token = f.read()
                LOGGER.debug('load: path=%s, token=%s', TOKEN_PATH, self._token)
        except:
            self._token = None
            pass

    def check(self):
        curtime = time.time()
        scan_interval = curtime - self._lastime
        if scan_interval < self._scan_interval:
            LOGGER.debug('updateIgnore: lastime=%d, elapse=%d', self._lastime, scan_interval)
        else:
            LOGGER.debug('updateData: curtime=%d, elapse=%d', curtime, scan_interval)
            self.update()
            self._lastime = curtime# time.time()

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
from homeassistant.const import (CONF_NAME, CONF_USERNAME, CONF_PASSWORD, CONF_SENSORS, CONF_OPTIMISTIC, CONF_SCAN_INTERVAL)
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_SENSORS, default=1): vol.Coerce(int),
    vol.Optional(CONF_OPTIMISTIC, default=True): cv.boolean,
    vol.Optional(CONF_SCAN_INTERVAL, default=0): vol.Coerce(int),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    name = config.get(CONF_NAME)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    sensors = config.get(CONF_SENSORS)
    optimistic = config.get(CONF_OPTIMISTIC)
    scan_interval = config.get(CONF_SCAN_INTERVAL)
    LOGGER.debug('setup_platform: name=%s, username=%s, password=%s, sensors=%d, optimistic=%s, scan_interval=%d', name, username, password, sensors, optimistic, scan_interval)

    AirCatSensor._data = AirCatData(username, password, scan_interval)
    AirCatSensor._optimistic = optimistic

    i = 0
    devices = []
    prop_unit_icons = [('pm25', 'μg/m³', 'blur'), ('hcho', 'mg/m³', 'biohazard'), ('temperature', '℃', 'thermometer'), ('humidity', '%', 'water-percent')]
    while i < sensors:
        for prop,unit,icon in prop_unit_icons:
            devices.append(AirCatSensor(name, i, prop, unit, icon))
            if not optimistic:
                break
        i += 1
    add_devices(devices, True)

class AirCatSensor(Entity):
    _data = None
    _optimistic = True

    def __init__(self, name, index, prop, unit, icon):
        if index:
            name += str(index + 1)
        if AirCatSensor._optimistic:
            name += ' ' + prop
        self._name = name
        self._index = index
        self._prop = prop
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
        return attributes[self._prop] if attributes else None

    @property
    def state_attributes(self):
        return None if AirCatSensor._optimistic else self.attributes

    @property
    def attributes(self):
        if AirCatSensor._data._devs and self._index < len(AirCatSensor._data._devs):
            return AirCatSensor._data._devs[self._index]['catDev']
        return None

    def update(self):
        if self._index == 0 and self._prop == 'pm25':
            AirCatSensor._data.check()

