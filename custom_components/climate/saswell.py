"""
Saswell platform that offers a Saswell climate device.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/climate/saswell
"""

import asyncio
import logging

from datetime import timedelta

import time
import voluptuous as vol

from homeassistant.components.climate import (
    ClimateDevice, SUPPORT_TARGET_TEMPERATURE, SUPPORT_AWAY_MODE,
     SUPPORT_ON_OFF, SUPPORT_OPERATION_MODE)
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL,
    ATTR_TEMPERATURE)
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

TOKEN_FILE = ".saswell.token."
USER_AGENT = "Thermostat/3.1.0 (iPhone; iOS 11.3; Scale/3.00)"

AUTH_URL = "http://api.scinan.com/oauth2/authorize?client_id=100002" \
    "&passwd=%s&redirect_uri=http%%3A//localhost.com%%3A8080" \
    "/testCallBack.action&response_type=token&userId=%s"
LIST_URL = "http://api.scinan.com/v1.0/devices/list?format=json"
CTRL_URL = "http://api.scinan.com/v1.0/sensors/control?" \
    "control_data=%%7B%%22value%%22%%3A%%22%s%%22%%7D&device_id=%s" \
    "&format=json&sensor_id=%s&sensor_type=1"

CONF_TEMPERATURE = 'temperature'
CONF_TARGET_TEMPERATURE = 'target_temperature'
CONF_OPERATION = 'operation'
CONF_AWAY = 'away'
CONF_IS_ON = 'is_on'

CONF_OPERATION_LIST = 'operation_list'
CONF_FAN_LIST = 'fan_list'
CONF_SWING_LIST = 'swing_list'

DEFAULT_NAME = 'Saswell'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_SCAN_INTERVAL, default=timedelta(seconds=300)): (
        vol.All(cv.time_period, cv.positive_timedelta)),
})


async def async_setup_platform(hass, config, async_add_devices,
                               discovery_info=None):
    """Set up the Saswell climate devices."""
    name = config.get(CONF_NAME)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    scan_interval = config.get(CONF_SCAN_INTERVAL)

    saswell = SaswellData(hass, username, password)
    await saswell.update_data()
    if not saswell.devs:
        _LOGGER.error("No sensors added: %s.", name)
        return None

    devices = []
    for index in range(len(saswell.devs)):
        devices.append(SaswellClimate(saswell, name, index))
    async_add_devices(devices)

    saswell.devices = devices
    async_track_time_interval(hass, saswell.async_update, scan_interval)


class SaswellClimate(ClimateDevice):
    """Representation of a Saswell climate device."""

    def __init__(self, saswell, name, index):
        """Initialize the climate device."""
        if index:
            name += str(index + 1)
        self._name = name
        self._index = index
        self._saswell = saswell

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def available(self):
        """Return if the sensor data are available."""
        return self.get_value('online')

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_AWAY_MODE | \
            SUPPORT_ON_OFF | SUPPORT_OPERATION_MODE

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self.unit_of_measurement

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.get_value(CONF_TEMPERATURE)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.get_value(CONF_TARGET_TEMPERATURE)

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return 'heat' if self.is_on else 'off'

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return ['heat', 'off']

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self.get_value(CONF_AWAY)

    @property
    def is_on(self):
        """Return true if the device is on."""
        return self.get_value(CONF_IS_ON)

    @property
    def should_poll(self):  # pylint: disable=no-self-use
        """No polling needed."""
        return False

    async def async_set_temperature(self, **kwargs):
        """Set new target temperatures."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            await self.set_value(CONF_TARGET_TEMPERATURE, temperature)

    async def async_set_operation_mode(self, operation_mode):
        """Set new target temperature."""
        if operation_mode == 'off':
            await self.set_value(CONF_IS_ON, False)
        else:
            await self.set_value(CONF_IS_ON, True)

    async def async_turn_away_mode_on(self):
        """Turn away mode on."""
        await self.set_value(CONF_AWAY, True)

    async def async_turn_away_mode_off(self):
        """Turn away mode off."""
        await self.set_value(CONF_AWAY, False)

    async def async_turn_on(self):
        """Turn on."""
        await self.set_value(CONF_IS_ON, True)

    async def async_turn_off(self):
        """Turn off."""
        await self.set_value(CONF_IS_ON, False)

    def get_value(self, prop):
        """Get property value"""
        devs = self._saswell.devs
        if devs and self._index < len(devs):
            return devs[self._index][prop]
        return None

    async def set_value(self, prop, value):
        """Set property value"""
        if await self._saswell.control(self._index, prop, value):
            self.async_schedule_update_ha_state()


class SaswellData():
    """Class for handling the data retrieval."""

    def __init__(self, hass, username, password):
        """Initialize the data object."""
        self._hass = hass
        self._username = username.replace('@', '%40')
        self._password = password
        self._token_path = hass.config.path(TOKEN_FILE + username)
        self.devs = None

        try:
            with open(self._token_path) as file:
                self._token = file.read()
                _LOGGER.debug("Load token: %s", self._token_path)
        except BaseException:
            self._token = None

    async def async_update(self, time):
        """Update online data and update ha state."""
        old_devs = self.devs
        await self.update_data()

        tasks = []
        index = 0
        for device in self.devices:
            if not old_devs or not self.devs \
                    or old_devs[index] != self.devs[index]:
                _LOGGER.info('%s: => %s', device.name, device.state)
                tasks.append(device.async_update_ha_state())

        if tasks:
            await asyncio.wait(tasks, loop=self._hass.loop)

    async def update_data(self):
        """Update online data."""
        try:
            json = await self.request(LIST_URL)
            if ('error' in json) and (json['error'] != '0'):
                _LOGGER.debug("Reset token: error=%s", json['error'])
                self._token = None
                json = await self.request(LIST_URL)
            devs = []
            for dev in json:
                status = dev['status'].split(',')
                devs.append({'is_on': status[1] == '1',
                             'away': status[5] == '1', #8?
                             'temperature': float(status[2]),
                             'target_temperature': float(status[3]),
                             'online': dev['online'] == '1',
                             'id': dev['id']})
            self.devs = devs
            _LOGGER.info("List device: devs=%s", self.devs)
        except BaseException:
            import traceback
            _LOGGER.error('Exception: %s', traceback.format_exc())

    async def control(self, index, prop, value):
        """Control device via server."""
        try:
            if prop == 'is_on':
                sensor_id = '01'
                data = '1' if value else '0'
            elif prop == 'target_temperature':
                sensor_id = '02'
                data = value
            elif prop == 'away':
                sensor_id = '03'
                data = '1' if value else '0'
            else:
                return False

            device_id = self.devs[index]['id']
            json = await self.request(CTRL_URL % (data, device_id, sensor_id))
            _LOGGER.debug("Control device: prop=%s, json=%s", prop, json)
            if json['result']:
                self.devs[index][prop] = value
                return True
            return False
        except BaseException:
            import traceback
            _LOGGER.error('Exception: %s', traceback.format_exc())
            return False

    async def request(self, url):
        """Request from server."""
        session = self._hass.helpers.aiohttp_client.async_get_clientsession()
        if self._token is None:
            headers = {'User-Agent': USER_AGENT}
            url = AUTH_URL % (self._password, self._username)
            async with session.get(url, headers=headers) as response:
                text = await response.text()
            _LOGGER.info("Get token: %s", text)
            start = text.find('token:')
            if start == -1 :
                return None

            start += 6
            end = text.find('\n', start) - 1
            self._token = text[start:end]
            with open(self._token_path, 'w') as file:
                file.write(self._token)

        headers = {'User-Agent': USER_AGENT}
        url += "&timestamp=%s&token=%s" % \
            (time.strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S'), self._token)
        _LOGGER.debug("URL: %s", url)
        async with session.get(url, headers=headers) as response:
            return await response.json(content_type=None)
