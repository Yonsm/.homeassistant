"""
Saswell platform that offers a fake climate device.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/climate/saswell
"""


from datetime import timedelta
from homeassistant.components.climate import (
    ClimateDevice, SUPPORT_TARGET_TEMPERATURE, SUPPORT_AWAY_MODE,
    SUPPORT_ON_OFF, SUPPORT_OPERATION_MODE)
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_USERNAME, CONF_PASSWORD,
    CONF_DEVICES,TEMP_CELSIUS, ATTR_TEMPERATURE)

import homeassistant.helpers.config_validation as cv
import logging
import requests
import time
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

TOKEN_FILE = ".saswell.token."
USER_AGENT = "Thermostat/3.1.0 (iPhone; iOS 11.3; Scale/3.00)"

AUTH_URL = "http://api.scinan.com/oauth2/authorize?client_id=100002&passwd=%s&redirect_uri=http%%3A//localhost.com%%3A8080/testCallBack.action&response_type=token&userId=%s"
LIST_URL = "http://api.scinan.com/v1.0/devices/list?format=json"
CTRL_URL = "http://api.scinan.com/v1.0/sensors/control?control_data=%%7B%%22value%%22%%3A%%22%s%%22%%7D&device_id=%s&format=json&sensor_id=%s&sensor_type=1"

DEFAULT_NAME = 'Saswell'

SCAN_INTERVAL = timedelta(seconds=300)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_DEVICES, default=1): cv.positive_int,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Saswell climate devices."""
    name = config.get(CONF_NAME)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    count = config.get(CONF_DEVICES)

    saswell = SaswellData(hass.config.path(TOKEN_FILE + username),
                          username, password, count)

    index = 0
    devices = []
    while index < count:
        devices.append(SaswellClimate(saswell, name, index))
        index += 1
    add_devices(devices, True)


class SaswellClimate(ClimateDevice):
    """Representation of a demo climate device."""

    def __init__(self, saswell, name, index):
        """Initialize the climate device."""
        if index:
            name += str(index + 1)
        self._name = name
        self._index = index
        self.saswell = saswell

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_AWAY_MODE | \
            SUPPORT_ON_OFF | SUPPORT_OPERATION_MODE

    #@property
    #def should_poll(self):
        """Return the polling state."""
    #    return True

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def available(self):
        """Return if the sensor data are available."""
        return self.get_prop('online', False)

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.get_prop('current', 0)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.get_prop('target', 20)

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self.get_prop('away', False)

    @property
    def is_on(self):
        """Return true if the device is on."""
        return self.get_prop('on', False)

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return 'heat' if self.is_on else 'off'

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return ['heat', 'off']

    def set_operation_mode(self, operation_mode):
        """Set new target temperature."""
        if operation_mode == 'off':
            self.turn_off()
        else:
            self.turn_on()
        self.schedule_update_ha_state()

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self.set_prop('target', kwargs.get(ATTR_TEMPERATURE))
        self.schedule_update_ha_state()

    def turn_away_mode_on(self):
        """Turn away mode on."""
        self.set_prop('away', True)
        self.schedule_update_ha_state()

    def turn_away_mode_off(self):
        """Turn away mode off."""
        self.set_prop('away', False)
        self.schedule_update_ha_state()

    def turn_on(self):
        """Turn on."""
        self.set_prop('on', True)
        self.schedule_update_ha_state()

    def turn_off(self):
        """Turn off."""
        self.set_prop('on', False)
        self.schedule_update_ha_state()

    def update(self):
        """Get the latest data from Phicomm server and update the state."""
        _LOGGER.info("Begin update: %s", self.name)
        self.saswell.update()

    def get_prop(self, prop, default):
        """Get property with current device index."""
        devs = self.saswell.devs
        if devs and self._index < len(devs):
            return devs[self._index][prop]
        return default

    def set_prop(self, prop, value):
        """Set property with current device index."""
        self.saswell.control(self._index, prop, value)


class SaswellData():
    """Class for handling the data retrieval."""

    def __init__(self, token_path, username, password, update_cycle):
        """Initialize the data object."""
        self._username = username
        self._password = password
        self._token_path = token_path
        self._update_cycle = update_cycle
        self._update_times = 0
        self.devs = None

        try:
            with open(self._token_path) as file:
                self._token = file.read()
                _LOGGER.debug("Load: %s => %s", self._token_path, self._token)
        except BaseException:
            self._token = None

    def update(self):
        """Update and handle data from Phicomm server."""
        if self._update_times % self._update_cycle == 0:
            try:
                json = self.list()
                if ('error' in json) and (json['error'] != '0'):
                    _LOGGER.debug("Reset token: error=%s", json['error'])
                    self._token = None
                    json = self.list()
                devs = []
                for dev in json:
                    status = dev['status'].split(',')
                    devs.append({'on': status[1] == '1',
                                 'away': status[5] == '1', #8?
                                 'current': float(status[2]),
                                 'target': float(status[3]),
                                 'online': dev['online'] == '1',
                                 'id': dev['id']})
                self.devs = devs
                _LOGGER.info("List device: devs=%s", self.devs)
            except BaseException:
                import traceback
                _LOGGER.error('Exception: %s', traceback.format_exc())

        self._update_times += 1

    def list(self):
        """Fetch the latest data from server."""
        return self.request(LIST_URL)

    def control(self, index, prop, value):
        """Control device via server."""
        try:
            if prop == 'on':
                sensor_id = '01'
                data = '1' if value else '0'
            elif prop == 'target':
                sensor_id = '02'
                data = value
            elif prop == 'away':
                sensor_id = '03'
                data = '1' if value else '0'
            else:
                return False

            device_id = self.devs[index]['id']
            json = self.request(CTRL_URL % (data, device_id, sensor_id))
            _LOGGER.debug("Control device: json=%s", json)
            if json['result']:
                self.devs[index][prop] = value
                time.sleep(1)
                return True
            return False
        except BaseException:
            import traceback
            _LOGGER.error('Exception: %s', traceback.format_exc())
            return False

    def request(self, url):
        """Request from server."""
        if self._token is None:
            headers = {'User-Agent': USER_AGENT}
            url = AUTH_URL % (self._password, self._username.replace('@', '%40'))
            text = requests.get(url, headers=headers).text
            _LOGGER.info("Get token: %s", text)
            start = text.find('token:')
            if start != -1 :
                start += 6
                end = text.find('\n', start) - 1
                self._token = text[start:end]
                with open(self._token_path, 'w') as file:
                    file.write(self._token)
            else:
                return None
        headers = {'User-Agent': USER_AGENT}
        url += "&timestamp=%s&token=%s" % \
            (time.strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S'), self._token)
        _LOGGER.debug("URL: %s", url)
        return requests.get(url, headers=headers).json()
