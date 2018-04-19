"""
Platform for a Generic Modbus Thermostat.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.modbus/
"""

from homeassistant.components.climate import (
    ClimateDevice, SUPPORT_TARGET_TEMPERATURE, SUPPORT_TARGET_HUMIDITY,
    SUPPORT_OPERATION_MODE, SUPPORT_FAN_MODE, SUPPORT_SWING_MODE,
    SUPPORT_HOLD_MODE, SUPPORT_AWAY_MODE, SUPPORT_AUX_HEAT, SUPPORT_ON_OFF,
    SUPPORT_TARGET_HUMIDITY_HIGH, SUPPORT_TARGET_HUMIDITY_LOW,
    PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, ATTR_TEMPERATURE)

import homeassistant.components.modbus as modbus
import homeassistant.helpers.config_validation as cv
import logging
import struct
import time
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['modbus']

DEFAULT_NAME = 'Modbus'

CONF_FEATURES = {
    'current_temperature': 0,
    'temperature': SUPPORT_TARGET_TEMPERATURE,
    'current_humidity': 0,
    'humidity': SUPPORT_TARGET_HUMIDITY |
                SUPPORT_TARGET_HUMIDITY_LOW |
                SUPPORT_TARGET_HUMIDITY_HIGH,
    'operation': SUPPORT_OPERATION_MODE,
    'fan': SUPPORT_FAN_MODE,
    'swing': SUPPORT_SWING_MODE,
    'hold': SUPPORT_HOLD_MODE,
    'away': SUPPORT_AWAY_MODE,
    'aux': SUPPORT_AUX_HEAT,
    'is_on': SUPPORT_ON_OFF
    }


CONF_OPERATION_LIST = 'operation_list'
CONF_FAN_LIST = 'fan_list'
CONF_SWING_LIST = 'swing_list'

DEFAULT_OPERATION_LIST = ['heat', 'cool', 'auto', 'off']
DEFAULT_FAN_LIST = ['On Low', 'On High', 'Auto Low', 'Auto High', 'Off']
DEFAULT_SWING_LIST = ['Auto', '1', '2', '3', 'Off']


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_OPERATION_LIST, default=DEFAULT_OPERATION_LIST): vol.All(cv.ensure_list, vol.Length(min=2)),
    vol.Optional(CONF_FAN_LIST, default=DEFAULT_FAN_LIST): vol.All(cv.ensure_list, vol.Length(min=2)),
    vol.Optional(CONF_SWING_LIST, default=DEFAULT_SWING_LIST): vol.All(cv.ensure_list, vol.Length(min=2)),
})


def has_valid_register(mods, index):
    for key in mods:
        registers = mods[key].get('registers')
        if not registers or index >= len(registers):
            return False
    return True

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Modbus climate devices."""
    name = config.get(CONF_NAME)
    operation_list = config.get(CONF_OPERATION_LIST)
    fan_list = config.get(CONF_FAN_LIST)
    swing_list = config.get(CONF_SWING_LIST)

    data_types = {'int': {1: 'h', 2: 'i', 4: 'q'}}
    data_types['uint'] = {1: 'H', 2: 'I', 4: 'Q'}
    data_types['float'] = {1: 'e', 2: 'f', 4: 'd'}

    mods = {}
    for key in CONF_FEATURES:
        mod = config.get(key)
        if not mod:
            continue

        count = mod['count'] if 'count' in mod else 1
        data_type = mod.get('data_type')
        if data_type != 'custom':
            try:
                mod['structure'] = '>{}'.format(data_types[
                    'int' if data_type is None else data_type][count])
            except KeyError:
                _LOGGER.error("Unable to detect data type for %s", key)
                continue

        try:
            size = struct.calcsize(mod['structure'])
        except struct.error as err:
            _LOGGER.error(
                "Error in sensor %s structure: %s", key, err)
            continue

        if count * 2 != size:
            _LOGGER.error(
                "Structure size (%d bytes) mismatch registers count "
                "(%d words)", size, count)
            continue

        mods[key] = mod

    if len(mods) == 0:
        _LOGGER.error("Invalid config %s: no modbus items", name)
        return

    devices = []
    for index in range(100):
        if not has_valid_register(mods, index):
            break
        devices.append(ModbusClimate(name, operation_list, fan_list, swing_list, mods, index))

    if len(devices) == 0:
        for key in mods:
            if 'register' not in mod:
                _LOGGER.error("Invalid config %s/%s: no register", name, key)
                return
        devices.append(ModbusClimate(name, operation_list, fan_list, swing_list, mods))

    add_devices(devices, True)


class ModbusClimate(ClimateDevice):
    """Representation of a Modbus climate device."""

    def __init__(self, name, operation_list, fan_list, swing_list, mods, index=-1):
        """Initialize the climate device."""
        self._name = name + str(index + 1) if index != -1 else name
        self._index = index
        self._mods = mods
        self._operation_list = operation_list
        self._fan_list = fan_list
        self._swing_list = swing_list
        self._values = {} # mods[key].get('default_value') for key in mods

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return self.unit_of_measurement

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1

    @property
    def supported_features(self):
        """Return the list of supported features."""
        features = 0
        for key in self._mods:
            features |= CONF_FEATURES[key]
        return features

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.get_value('current_temperature')

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.get_value('temperature')

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self.get_value('current_humidity')

    @property
    def target_humidity(self):
        """Return the humidity we try to reach."""
        return self.get_value('humidity')

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        operation = self.get_value('operation')
        return self._operation_list[operation] if operation is not None and  operation < len(self._operation_list) else None

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        fan = self.get_value('fan')
        return self._fan_list[fan] if fan is not None and fan < len(self._fan_list) else None

    @property
    def fan_list(self):
        """Return the list of available fan modes."""
        return self._fan_list

    @property
    def current_swing_mode(self):
        """Return the swing setting."""
        swing = self.get_value('swing')
        return self._swing_list[swing] if swing is not None and swing < len(self._swing_list) else None

    @property
    def swing_list(self):
        """List of available swing modes."""
        return self._swing_list

    @property
    def current_hold_mode(self):
        """Return hold mode setting."""
        return self.get_value('hold')

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self.get_value('away')

    @property
    def is_aux_heat_on(self):
        """Return true if aux heat is on."""
        return self.get_value('aux')

    @property
    def is_on(self):
        """Return true if the device is on."""
        return self.get_value('is_on')

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self.set_value('temperature', kwargs.get(ATTR_TEMPERATURE))

    def set_humidity(self, humidity):
        """Set new target humidity."""
        self.set_value('humidity', humidity)

    def set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        try:
            index = self._operation_list.index(operation_mode)
            self.set_value('operation', index)
        except ValueError:
            _LOGGER.error("Invalid operation_mode: %s", operation_mode)

    def set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        try:
            index = self._fan_list.index(fan_mode)
            self.set_value('fan', index)
        except ValueError:
            _LOGGER.error("Invalid fan_mode: %s", fan_mode)

    def set_swing_mode(self, swing_mode):
        """Set new swing mode."""
        try:
            index = self._swing_list.index(swing_mode)
            self.set_value('swing', index)
        except ValueError:
            _LOGGER.error("Invalid swing_mode: %s", swing_mode)

    def set_hold_mode(self, hold_mode):
        """Set new hold mode."""
        self.set_value('hold', hold_mode)

    def turn_away_mode_on(self):
        """Turn away mode on."""
        self.set_value('away', True)

    def turn_away_mode_off(self):
        """Turn away mode off."""
        self.set_value('away', False)

    def turn_aux_heat_on(self):
        """Turn auxiliary heater on."""
        self.set_value('aux', True)

    def turn_aux_heat_off(self):
        """Turn auxiliary heater off."""
        self.set_value('aux', False)

    def turn_on(self):
        """Turn on."""
        self.set_value('is_on', True)

    def turn_off(self):
        """Turn off."""
        self.set_value('is_on', False)

    def update(self):
        """Update state."""
        for key in self._mods:
            mod = self._mods[key]

            register_type = mod.get('register_type')
            slave = mod['slave'] if 'slave' in mod else 1
            register = mod['register'] if self._index == -1 else mod['registers'][self._index]
            count = mod['count'] if 'count' in mod else 1

            if register_type == 'coil':
                result = modbus.HUB.read_coils(slave, register, count)
                value = bool(result.bits[0])
            else:
                if register_type == 'input':
                    result = modbus.HUB.read_input_registers(slave,
                                                             register, count)
                else:
                    result = modbus.HUB.read_holding_registers(slave,
                                                               register, count)

                val = 0
                try:
                    registers = result.registers
                    if mod.get('reverse_order'):
                        registers.reverse()
                except AttributeError:
                    _LOGGER.error("No response from modbus %s", key)
                    return

                byte_string = b''.join(
                    [x.to_bytes(2, byteorder='big') for x in registers]
                )
                val = struct.unpack(mod['structure'], byte_string)[0]
                scale = mod['scale'] if 'scale' in mod else 1
                offset = mod['offset'] if 'offset' in mod else 0
                value = scale * val + offset

            _LOGGER.info("Read %s: %s = %f", self.name, key, value)
            self._values[key] = value

    def get_value(self, key):
        return self._values.get(key)

    def set_value(self, key, value):
        mod = self._mods[key]
        _LOGGER.info("Write %s: %s = %f", self.name, key, value)

        register_type = mod.get('register_type')
        slave = mod['slave'] if 'slave' in mod else 1
        register = mod['register'] if self._index == -1 else mod['registers'][self._index]

        if register_type == 'coil':
            modbus.HUB.write_coil(slave, register, bool(value))
        else:
            modbus.HUB.write_register(slave, register, int(value))

        self._values[key] = value
        self.schedule_update_ha_state()
