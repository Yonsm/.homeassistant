import asyncio
import logging
import binascii
import socket
import os.path
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.cover import (CoverEntity, PLATFORM_SCHEMA, SUPPORT_OPEN, SUPPORT_CLOSE)
from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_MAC, CONF_TIMEOUT, STATE_OPEN, STATE_CLOSED)
from homeassistant.helpers.event import track_utc_time_change
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.core import callback
from configparser import ConfigParser
from base64 import b64encode, b64decode

REQUIREMENTS = ['broadlink==0.11.1']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Broadlink Cover'
DEFAULT_TIMEOUT = 10

CONF_COMMAND_OPEN = 'command_open'
CONF_COMMAND_CLOSE = 'command_close'
CONF_COMMAND_STOP = 'command_stop'
CONF_POS_SENSOR = 'position_sensor'
CONF_TRAVEL_TIME = 'travel_time'
CONF_COVERS = 'covers'

COVERS_SCHEMA = vol.Schema({
    vol.Optional(CONF_COMMAND_STOP, default=None): cv.string,
    vol.Optional(CONF_COMMAND_OPEN, default=None): cv.string,
    vol.Optional(CONF_COMMAND_CLOSE, default=None): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TRAVEL_TIME, default=None): cv.positive_int,
#    vol.Optional(CONF_POS_SENSOR, default=None): cv.entity_id,
    vol.Optional(CONF_POS_SENSOR,): cv.entity_id,
})


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_COVERS, default={}):
        vol.Schema({cv.slug: COVERS_SCHEMA}),
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_MAC): cv.string,
})

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    import broadlink
    devices = config.get(CONF_COVERS)
    ip_addr = config.get(CONF_HOST)
    mac_addr = binascii.unhexlify(
        config.get(CONF_MAC).encode().replace(b':', b''))
    broadlink_device = broadlink.rm((ip_addr, 80), mac_addr, None)

    covers = []
    for object_id, device_config in devices.items():
        covers.append(
            RMCover(
                hass,
                object_id,
                broadlink_device,
                device_config.get(CONF_NAME,object_id),
                device_config.get(CONF_COMMAND_OPEN),
                device_config.get(CONF_COMMAND_CLOSE),
                device_config.get(CONF_COMMAND_STOP),
                device_config.get(CONF_TRAVEL_TIME),
                device_config.get(CONF_POS_SENSOR),
            )
        )

    broadlink_device.timeout = config.get(CONF_TIMEOUT)
    try:
        broadlink_device.auth()
    except socket.timeout:
        _LOGGER.error("Failed to connect to Broadlink RM Device")

    async_add_devices(covers, True)
    return True


class RMCover(CoverEntity,RestoreEntity):
    """Representation of a cover."""

    # pylint: disable=no-self-use
    def __init__(self, hass, entity_id, device, name, cmd_open, cmd_close,
                    cmd_stop, travel_time, pos_entity_id):
        """Initialize the cover."""
        self.hass = hass
        self.entity_id = async_generate_entity_id(
            'cover.{}', entity_id, hass=hass)
        self._name = name or entity_id

        if travel_time:
            self._position = 50
            self._travel_time = travel_time
            self._step = round(100.0 / travel_time ,2)
            self._device_class = 'window'
        else:
            self._position = None
            self._device_class = 'garage'

        self._cmd_open = b64decode(cmd_open) if cmd_open else None
        self._cmd_close = b64decode(cmd_close) if cmd_close else None
        if cmd_stop:
            self._cmd_stop = b64decode(cmd_stop)
            self._supported_features=None
        else:
            self._position = None
            self._supported_features=(SUPPORT_OPEN | SUPPORT_CLOSE)
            self._device_class = 'garage'

        self._requested_closing = True
        self._unsub_listener_cover = None
        self._is_opening = False
        self._is_closing = False
        self._device = device
        self._travel = 0
        self._closed = False
        self._delay = False

        if pos_entity_id:
            async_track_state_change(
                hass, pos_entity_id, self._async_pos_changed)

            temp_state = hass.states.get(pos_entity_id)
            if temp_state:
                self._async_update_pos(temp_state)

    @callback
    def _async_update_pos(self, state):
        if state.state in ('false', STATE_CLOSED, 'off'):
            if self._device_class == 'window':
                self._position = 0
            self._closed = True
        else:
            self._closed = False
            if self._position == 0:
                self._position = 100


    @asyncio.coroutine
    def _async_pos_changed(self, entity_id, old_state, new_state):
        if new_state is None:
            return
        self._async_update_pos(new_state)
        yield from self.async_update_ha_state()


    @property
    def device_state_attributes(self):
        if self._device_class == 'window':
            return {'homebridge_cover_type': 'rollershutter'}
        else:
            return {'homebridge_cover_type': 'garage_door'}

    @property
    def name(self):
        """Return the name of the cover."""
        return self._name

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._device_class

    @property
    def supported_features(self):
        """Flag supported features."""
        if self._supported_features is not None:
            return self._supported_features
        return super().supported_features

    @property
    def should_poll(self):
        """No polling needed for a demo cover."""
        return False

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return self._position

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self._position is None:
            return self._closed
        else:
            return self._position == 0

    @property
    def is_closing(self):
        """Return if the cover is closing."""
        return self._is_closing

    @property
    def is_opening(self):
        """Return if the cover is opening."""
        return self._is_opening

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._device_class

    def close_cover(self, **kwargs):
        """Close the cover."""
        if self._position == 0:
            return
        elif self._position is None:
            if self._sendpacket(self._cmd_close):
                self._closed = True
                self.schedule_update_ha_state()
            return

        if self._sendpacket(self._cmd_close):
            self._travel = self._travel_time + 1
            self._is_closing = True
            self._listen_cover()
            self._requested_closing = True
            self.schedule_update_ha_state()

    def open_cover(self, **kwargs):
        """Open the cover."""
        if self._position == 100:
            return
        elif self._position is None:
            if self._sendpacket(self._cmd_open):
                self._closed = False
                self.schedule_update_ha_state()
            return

        if self._sendpacket(self._cmd_open):
            self._travel = self._travel_time + 1
            self._is_opening = True
            self._listen_cover()
            self._requested_closing = False
            self.schedule_update_ha_state()

    def set_cover_position(self, position, **kwargs):
        """Move the cover to a specific position."""
        if position <= 0:
            self.close_cover()
        elif position >= 100:
            self.open_cover()
        elif round(self._position) == round(position):
            return
        elif self._travel > 0:
            return
        else:
            steps = abs((position - self._position) / self._step)
            if steps >= 1:
                self._travel = round(steps, 0)
            else:
                self._travel = 1
            self._requested_closing = position < self._position
            if self._requested_closing:
                if self._sendpacket(self._cmd_close):
                    self._listen_cover()
            else:
                if self._sendpacket(self._cmd_open):
                    self._listen_cover()


    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self._is_closing = False
        self._is_opening = False
        if self._position is None:
            self._sendpacket(self._cmd_stop)
            return
        elif self._position > 0 and self._position < 100:
                self._sendpacket(self._cmd_stop)

        if self._unsub_listener_cover is not None:
            self._unsub_listener_cover()
            self._unsub_listener_cover = None

    def _listen_cover(self):
        """Listen for changes in cover."""
        if self._unsub_listener_cover is None:
            self._unsub_listener_cover = track_utc_time_change(
                self.hass, self._time_changed_cover)
            self._delay = True

    def _time_changed_cover(self, now):
        """Track time changes."""
        if self._delay:
            self._delay = False
        else:
            if self._requested_closing:
                if round(self._position - self._step) > 0:
                    self._position -= self._step
                else:
                    self._position = 0
                    self._travel = 0
            else:
                if round(self._position + self._step) < 100:
                    self._position += self._step
                else:
                    self._position = 100
                    self._travel = 0

            self._travel -= 1

            if self._travel <= 0:
                self.stop_cover()

            self.schedule_update_ha_state()


    def _sendpacket(self, packet, retry=2):
        """Send packet to device."""
        if packet is None:
            _LOGGER.debug("Empty packet")
            return True
        try:
            self._device.send_data(packet)
        except (socket.timeout, ValueError) as error:
            if retry < 1:
                _LOGGER.error(error)
                return False
            if not self._auth():
                return False
            return self._sendpacket(packet, retry-1)
        return True

    def _auth(self, retry=2):
        try:
            auth = self._device.auth()
        except socket.timeout:
            auth = False
        if not auth and retry > 0:
            return self._auth(retry-1)
        return auth

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()

        if last_state:
            self._position = last_state.attributes['current_position']
