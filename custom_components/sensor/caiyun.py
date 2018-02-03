#!/usr/bin/env python
#encoding:utf8

import logging
import requests, json

# Const
USER_AGENT = 'ColorfulCloudsPro/3.2.0 (iPhone; iOS 11.2.2; Scale/2.00)'
LOGGER = logging.getLogger(__name__)

# Import homeassistant
from homeassistant.helpers.entity import Entity
from homeassistant.const import (CONF_NAME, CONF_OPTIMISTIC)
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default='CaiYun'): cv.string,
    vol.Optional(CONF_OPTIMISTIC, default=True): cv.boolean,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    name = config.get(CONF_NAME)
    optimistic = config.get(CONF_OPTIMISTIC)
    LOGGER.debug('setup_platform: name=%s, optimistic=%s', name, optimistic)

    CaiYunSensor._data = None
    CaiYunSensor._optimistic = optimistic

    devices = []
    prop_unit_icons = [('weather', None, None), ('pm25', 'μg/m³', 'blur'), ('aqi', None, 'leaf'), ('temperature', '℃', 'thermometer'), ('humidity', '%', 'water-percent'), ('rainfall', None, 'weather-pouring')]
    for prop,unit,icon in prop_unit_icons:
        devices.append(CaiYunSensor(name, prop, unit, icon))
        if not optimistic:
            break
    add_devices(devices, True)

class CaiYunSensor(Entity):

    def __init__(self, name, prop, unit, icon):
        if CaiYunSensor._optimistic:
            name += ' ' + prop
        self._name = name
        self._prop = prop
        self._unit = unit
        self._icon = 'mdi:' + icon if icon else None

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        if self._prop == 'weather' and self.available:
            return self.attributes['icon']
        return self._icon

    @property
    def unit_of_measurement(self):
        return self._unit

    @property
    def available(self):
        return CaiYunSensor._data and 'status' in CaiYunSensor._data and CaiYunSensor._data['status'] == 'ok'

    @property
    def state(self):
        attributes = self.attributes
        return attributes[self._prop] if attributes else None

    @property
    def state_attributes(self):
        return None if CaiYunSensor._optimistic else self.attributes

    @property
    def attributes(self):
        return CaiYunSensor._data['result'] if self.available else None

    def update(self):
        if self._prop == 'weather':
            LOGGER.debug('update: name=%s', self._name)
            headers = {'User-Agent': USER_AGENT}
            CaiYunSensor._data = requests.get('http://api.caiyunapp.com/v2/UR8ASaplvIwavDfR/120.05633,30.23927/realtime.json', headers=headers).json()
            attributes = self.attributes
            if attributes:
                attributes['pm25'] = int(attributes['pm25'])
                attributes['humidity'] = int(attributes['humidity'] * 100)
                skycon = attributes['skycon']
                state_icon = {
                'CLEAR_DAY': ('晴天','sunny'),
                'CLEAR_NIGHT': ('晴夜','night'),
                'PARTLY_CLOUDY_DAY': ('多云','partlycloudy'),
                'PARTLY_CLOUDY_NIGHT': ('多云','windy-variant'),
                'CLOUDY': ('阴','cloudy'),
                'RAIN': ('雨','rainy'),
                'SNOW': ('雪','snowy'),
                'WIND': ('风','windy'),
                'FOG': ('雾','fog'),
                'HAZE': ('霾','hail'),
                'SLEET': ('冻雨','snowy-rainy')
                }
                state,icon = state_icon[skycon]
                attributes['weather'] = state
                attributes['icon'] = 'mdi:weather-' + icon if icon else 'mdi:help-circle-outline'
                attributes['rainfall'] = attributes['precipitation']['local']['intensity']
                del(attributes['wind'])
                del(attributes['precipitation'])
