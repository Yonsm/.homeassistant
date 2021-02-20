"""Class to hold all thermostat accessories."""
import logging

from pyhap.const import CATEGORY_THERMOSTAT

from homeassistant.components.climate.const import (
    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HUMIDITY,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_HVAC_MODES,
    ATTR_MAX_TEMP,
    ATTR_MIN_HUMIDITY,
    ATTR_MIN_TEMP,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_DRY,
    CURRENT_HVAC_FAN,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_HUMIDITY,
    DEFAULT_MIN_TEMP,
    DOMAIN as DOMAIN_CLIMATE,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_HVAC_MODE as SERVICE_SET_HVAC_MODE_THERMOSTAT,
    SERVICE_SET_TEMPERATURE as SERVICE_SET_TEMPERATURE_THERMOSTAT,
    SUPPORT_TARGET_HUMIDITY,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from homeassistant.components.water_heater import (
    DOMAIN as DOMAIN_WATER_HEATER,
    SERVICE_SET_TEMPERATURE as SERVICE_SET_TEMPERATURE_WATER_HEATER,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    ATTR_TEMPERATURE,
    PERCENTAGE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    STATE_ON, SERVICE_TURN_OFF, SERVICE_TURN_ON, STATE_OFF,
)
from homeassistant.core import callback

from .accessories import TYPES, HomeAccessory
from .const import (
    CHAR_COOLING_THRESHOLD_TEMPERATURE,
    CHAR_CURRENT_HEATING_COOLING,
    CHAR_CURRENT_HUMIDITY,
    CHAR_CURRENT_TEMPERATURE,
    CHAR_HEATING_THRESHOLD_TEMPERATURE,
    CHAR_TARGET_HEATING_COOLING,
    CHAR_TARGET_HUMIDITY,
    CHAR_TARGET_TEMPERATURE,
    CHAR_TEMP_DISPLAY_UNITS,
    DEFAULT_MAX_TEMP_WATER_HEATER,
    DEFAULT_MIN_TEMP_WATER_HEATER,
    PROP_MAX_VALUE,
    PROP_MIN_VALUE,
    SERV_THERMOSTAT,
    CHAR_ACTIVE, SERV_FANV2,
)
from .util import temperature_to_homekit, temperature_to_states

_LOGGER = logging.getLogger(__name__)

DEFAULT_HVAC_MODES = [
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
]

HC_HOMEKIT_VALID_MODES_WATER_HEATER = {"Heat": 1}
UNIT_HASS_TO_HOMEKIT = {TEMP_CELSIUS: 0, TEMP_FAHRENHEIT: 1}

HC_HEAT_COOL_OFF = 0
HC_HEAT_COOL_HEAT = 1
HC_HEAT_COOL_COOL = 2
HC_HEAT_COOL_AUTO = 3

HC_HEAT_COOL_PREFER_HEAT = [
    HC_HEAT_COOL_AUTO,
    HC_HEAT_COOL_HEAT,
    HC_HEAT_COOL_COOL,
    HC_HEAT_COOL_OFF,
]

HC_HEAT_COOL_PREFER_COOL = [
    HC_HEAT_COOL_AUTO,
    HC_HEAT_COOL_COOL,
    HC_HEAT_COOL_HEAT,
    HC_HEAT_COOL_OFF,
]

HC_MIN_TEMP = 10
HC_MAX_TEMP = 38

UNIT_HOMEKIT_TO_HASS = {c: s for s, c in UNIT_HASS_TO_HOMEKIT.items()}
HC_HASS_TO_HOMEKIT = {
    HVAC_MODE_OFF: HC_HEAT_COOL_OFF,
    HVAC_MODE_HEAT: HC_HEAT_COOL_HEAT,
    HVAC_MODE_COOL: HC_HEAT_COOL_COOL,
    HVAC_MODE_AUTO: HC_HEAT_COOL_AUTO,
    HVAC_MODE_HEAT_COOL: HC_HEAT_COOL_AUTO,
    HVAC_MODE_DRY: HC_HEAT_COOL_COOL,
    HVAC_MODE_FAN_ONLY: HC_HEAT_COOL_COOL,
}
HC_HOMEKIT_TO_HASS = {c: s for s, c in HC_HASS_TO_HOMEKIT.items()}

HC_HASS_TO_HOMEKIT_ACTION = {
    CURRENT_HVAC_OFF: HC_HEAT_COOL_OFF,
    CURRENT_HVAC_IDLE: HC_HEAT_COOL_OFF,
    CURRENT_HVAC_HEAT: HC_HEAT_COOL_HEAT,
    CURRENT_HVAC_COOL: HC_HEAT_COOL_COOL,
    CURRENT_HVAC_DRY: HC_HEAT_COOL_COOL,
    CURRENT_HVAC_FAN: HC_HEAT_COOL_COOL,
}

HEAT_COOL_DEADBAND = 5


@TYPES.register("Thermostat")
class Thermostat0(HomeAccessory):
    """Generate a Thermostat accessory for a climate."""

    def __init__(self, *args):
        """Initialize a Thermostat accessory object."""
        super().__init__(*args, category=CATEGORY_THERMOSTAT)
        self._unit = self.hass.config.units.temperature_unit
        self.hc_homekit_to_hass = None
        self.hc_hass_to_homekit = None
        hc_min_temp, hc_max_temp = self.get_temperature_range()

        # Add additional characteristics if auto mode is supported
        self.chars = []
        state = self.hass.states.get(self.entity_id)
        min_humidity = state.attributes.get(ATTR_MIN_HUMIDITY, DEFAULT_MIN_HUMIDITY)
        features = state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

        if features & SUPPORT_TARGET_TEMPERATURE_RANGE:
            self.chars.extend(
                (CHAR_COOLING_THRESHOLD_TEMPERATURE, CHAR_HEATING_THRESHOLD_TEMPERATURE)
            )

        if features & SUPPORT_TARGET_HUMIDITY:
            self.chars.extend((CHAR_TARGET_HUMIDITY, CHAR_CURRENT_HUMIDITY))

        serv_thermostat = self.add_preload_service(SERV_THERMOSTAT, self.chars)

        # Current mode characteristics
        self.char_current_heat_cool = serv_thermostat.configure_char(
            CHAR_CURRENT_HEATING_COOLING, value=0
        )

        self._configure_hvac_modes(state)
        # Must set the value first as setting
        # valid_values happens before setting
        # the value and if 0 is not a valid
        # value this will throw
        self.char_target_heat_cool = serv_thermostat.configure_char(
            CHAR_TARGET_HEATING_COOLING, value=list(self.hc_homekit_to_hass)[0]
        )
        self.char_target_heat_cool.override_properties(
            valid_values=self.hc_hass_to_homekit
        )
        # Current and target temperature characteristics

        self.char_current_temp = serv_thermostat.configure_char(
            CHAR_CURRENT_TEMPERATURE, value=21.0
        )

        self.char_target_temp = serv_thermostat.configure_char(
            CHAR_TARGET_TEMPERATURE,
            value=21.0,
            # We do not set PROP_MIN_STEP here and instead use the HomeKit
            # default of 0.1 in order to have enough precision to convert
            # temperature units and avoid setting to 73F will result in 74F
            properties={PROP_MIN_VALUE: hc_min_temp, PROP_MAX_VALUE: hc_max_temp},
        )

        # Display units characteristic
        self.char_display_units = serv_thermostat.configure_char(
            CHAR_TEMP_DISPLAY_UNITS, value=0
        )

        # If the device supports it: high and low temperature characteristics
        self.char_cooling_thresh_temp = None
        self.char_heating_thresh_temp = None
        if CHAR_COOLING_THRESHOLD_TEMPERATURE in self.chars:
            self.char_cooling_thresh_temp = serv_thermostat.configure_char(
                CHAR_COOLING_THRESHOLD_TEMPERATURE,
                value=23.0,
                # We do not set PROP_MIN_STEP here and instead use the HomeKit
                # default of 0.1 in order to have enough precision to convert
                # temperature units and avoid setting to 73F will result in 74F
                properties={PROP_MIN_VALUE: hc_min_temp, PROP_MAX_VALUE: hc_max_temp},
            )
        if CHAR_HEATING_THRESHOLD_TEMPERATURE in self.chars:
            self.char_heating_thresh_temp = serv_thermostat.configure_char(
                CHAR_HEATING_THRESHOLD_TEMPERATURE,
                value=19.0,
                # We do not set PROP_MIN_STEP here and instead use the HomeKit
                # default of 0.1 in order to have enough precision to convert
                # temperature units and avoid setting to 73F will result in 74F
                properties={PROP_MIN_VALUE: hc_min_temp, PROP_MAX_VALUE: hc_max_temp},
            )
        self.char_target_humidity = None
        self.char_current_humidity = None
        if CHAR_TARGET_HUMIDITY in self.chars:
            self.char_target_humidity = serv_thermostat.configure_char(
                CHAR_TARGET_HUMIDITY,
                value=50,
                # We do not set a max humidity because
                # homekit currently has a bug that will show the lower bound
                # shifted upwards.  For example if you have a max humidity
                # of 80% homekit will give you the options 20%-100% instead
                # of 0-80%
                properties={PROP_MIN_VALUE: min_humidity},
            )
            self.char_current_humidity = serv_thermostat.configure_char(
                CHAR_CURRENT_HUMIDITY, value=50
            )

        self._async_update_state(state)

        serv_thermostat.setter_callback = self._set_chars

    def _temperature_to_homekit(self, temp):
        return temperature_to_homekit(temp, self._unit)

    def _temperature_to_states(self, temp):
        return temperature_to_states(temp, self._unit)

    def _set_chars(self, char_values):
        _LOGGER.debug("Thermostat _set_chars: %s", char_values)
        events = []
        params = {}
        service = None
        state = self.hass.states.get(self.entity_id)
        features = state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

        hvac_mode = state.state
        homekit_hvac_mode = HC_HASS_TO_HOMEKIT[hvac_mode]

        if CHAR_TARGET_HEATING_COOLING in char_values:
            # Homekit will reset the mode when VIEWING the temp
            # Ignore it if its the same mode
            if char_values[CHAR_TARGET_HEATING_COOLING] != homekit_hvac_mode:
                target_hc = char_values[CHAR_TARGET_HEATING_COOLING]
                if target_hc not in self.hc_homekit_to_hass:
                    # If the target heating cooling state we want does not
                    # exist on the device, we have to sort it out
                    # based on the the current and target temperature since
                    # siri will always send HC_HEAT_COOL_AUTO in this case
                    # and hope for the best.
                    hc_target_temp = char_values.get(CHAR_TARGET_TEMPERATURE)
                    hc_current_temp = _get_current_temperature(state, self._unit)
                    hc_fallback_order = HC_HEAT_COOL_PREFER_HEAT
                    if (
                        hc_target_temp is not None
                        and hc_current_temp is not None
                        and hc_target_temp < hc_current_temp
                    ):
                        hc_fallback_order = HC_HEAT_COOL_PREFER_COOL
                    for hc_fallback in hc_fallback_order:
                        if hc_fallback in self.hc_homekit_to_hass:
                            _LOGGER.debug(
                                "Siri requested target mode: %s and the device does not support, falling back to %s",
                                target_hc,
                                hc_fallback,
                            )
                            target_hc = hc_fallback
                            break

                service = SERVICE_SET_HVAC_MODE_THERMOSTAT
                hass_value = self.hc_homekit_to_hass[target_hc]
                params = {ATTR_HVAC_MODE: hass_value}
                events.append(
                    f"{CHAR_TARGET_HEATING_COOLING} to {char_values[CHAR_TARGET_HEATING_COOLING]}"
                )

        if CHAR_TARGET_TEMPERATURE in char_values:
            hc_target_temp = char_values[CHAR_TARGET_TEMPERATURE]
            if features & SUPPORT_TARGET_TEMPERATURE:
                service = SERVICE_SET_TEMPERATURE_THERMOSTAT
                temperature = self._temperature_to_states(hc_target_temp)
                events.append(
                    f"{CHAR_TARGET_TEMPERATURE} to {char_values[CHAR_TARGET_TEMPERATURE]}°C"
                )
                params[ATTR_TEMPERATURE] = temperature
            elif features & SUPPORT_TARGET_TEMPERATURE_RANGE:
                # Homekit will send us a target temperature
                # even if the device does not support it
                _LOGGER.debug(
                    "Homekit requested target temp: %s and the device does not support",
                    hc_target_temp,
                )
                if (
                    homekit_hvac_mode == HC_HEAT_COOL_HEAT
                    and CHAR_HEATING_THRESHOLD_TEMPERATURE not in char_values
                ):
                    char_values[CHAR_HEATING_THRESHOLD_TEMPERATURE] = hc_target_temp
                if (
                    homekit_hvac_mode == HC_HEAT_COOL_COOL
                    and CHAR_COOLING_THRESHOLD_TEMPERATURE not in char_values
                ):
                    char_values[CHAR_COOLING_THRESHOLD_TEMPERATURE] = hc_target_temp

        if (
            CHAR_HEATING_THRESHOLD_TEMPERATURE in char_values
            or CHAR_COOLING_THRESHOLD_TEMPERATURE in char_values
        ):
            service = SERVICE_SET_TEMPERATURE_THERMOSTAT
            high = self.char_cooling_thresh_temp.value
            low = self.char_heating_thresh_temp.value
            min_temp, max_temp = self.get_temperature_range()
            if CHAR_COOLING_THRESHOLD_TEMPERATURE in char_values:
                events.append(
                    f"{CHAR_COOLING_THRESHOLD_TEMPERATURE} to {char_values[CHAR_COOLING_THRESHOLD_TEMPERATURE]}°C"
                )
                high = char_values[CHAR_COOLING_THRESHOLD_TEMPERATURE]
                # If the device doesn't support TARGET_TEMPATURE
                # this can happen
                if high < low:
                    low = high - HEAT_COOL_DEADBAND
            if CHAR_HEATING_THRESHOLD_TEMPERATURE in char_values:
                events.append(
                    f"{CHAR_HEATING_THRESHOLD_TEMPERATURE} to {char_values[CHAR_HEATING_THRESHOLD_TEMPERATURE]}°C"
                )
                low = char_values[CHAR_HEATING_THRESHOLD_TEMPERATURE]
                # If the device doesn't support TARGET_TEMPATURE
                # this can happen
                if low > high:
                    high = low + HEAT_COOL_DEADBAND

            high = min(high, max_temp)
            low = max(low, min_temp)

            params.update(
                {
                    ATTR_TARGET_TEMP_HIGH: self._temperature_to_states(high),
                    ATTR_TARGET_TEMP_LOW: self._temperature_to_states(low),
                }
            )

        if service:
            params[ATTR_ENTITY_ID] = self.entity_id
            self.call_service(
                DOMAIN_CLIMATE,
                service,
                params,
                ", ".join(events),
            )

        if CHAR_TARGET_HUMIDITY in char_values:
            self.set_target_humidity(char_values[CHAR_TARGET_HUMIDITY])

    def _configure_hvac_modes(self, state):
        """Configure target mode characteristics."""
        # This cannot be none OR an empty list
        hc_modes = state.attributes.get(ATTR_HVAC_MODES) or DEFAULT_HVAC_MODES
        # Determine available modes for this entity,
        # Prefer HEAT_COOL over AUTO and COOL over FAN_ONLY, DRY
        #
        # HEAT_COOL is preferred over auto because HomeKit Accessory Protocol describes
        # heating or cooling comes on to maintain a target temp which is closest to
        # the Home Assistant spec
        #
        # HVAC_MODE_HEAT_COOL: The device supports heating/cooling to a range
        self.hc_homekit_to_hass = {
            c: s
            for s, c in HC_HASS_TO_HOMEKIT.items()
            if (
                s in hc_modes
                and not (
                    (s == HVAC_MODE_AUTO and HVAC_MODE_HEAT_COOL in hc_modes)
                    or (
                        s in (HVAC_MODE_DRY, HVAC_MODE_FAN_ONLY)
                        and HVAC_MODE_COOL in hc_modes
                    )
                )
            )
        }
        self.hc_hass_to_homekit = {k: v for v, k in self.hc_homekit_to_hass.items()}

    def get_temperature_range(self):
        """Return min and max temperature range."""
        return _get_temperature_range_from_state(
            self.hass.states.get(self.entity_id),
            self._unit,
            DEFAULT_MIN_TEMP,
            DEFAULT_MAX_TEMP,
        )

    def set_target_humidity(self, value):
        """Set target humidity to value if call came from HomeKit."""
        _LOGGER.debug("%s: Set target humidity to %d", self.entity_id, value)
        params = {ATTR_ENTITY_ID: self.entity_id, ATTR_HUMIDITY: value}
        self.call_service(
            DOMAIN_CLIMATE, SERVICE_SET_HUMIDITY, params, f"{value}{PERCENTAGE}"
        )

    @callback
    def async_update_state(self, new_state):
        """Update thermostat state after state changed."""
        # We always recheck valid hvac modes as the entity
        # may not have been fully setup when we saw it last
        original_hc_hass_to_homekit = self.hc_hass_to_homekit
        self._configure_hvac_modes(new_state)

        if self.hc_hass_to_homekit != original_hc_hass_to_homekit:
            if self.char_target_heat_cool.value not in self.hc_homekit_to_hass:
                # We must make sure the char value is
                # in the new valid values before
                # setting the new valid values or
                # changing them with throw
                self.char_target_heat_cool.set_value(
                    list(self.hc_homekit_to_hass)[0], should_notify=False
                )
            self.char_target_heat_cool.override_properties(
                valid_values=self.hc_hass_to_homekit
            )

        self._async_update_state(new_state)

    @callback
    def _async_update_state(self, new_state):
        """Update state without rechecking the device features."""
        features = new_state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

        # Update target operation mode FIRST
        hvac_mode = new_state.state
        if hvac_mode and hvac_mode in HC_HASS_TO_HOMEKIT:
            homekit_hvac_mode = HC_HASS_TO_HOMEKIT[hvac_mode]
            if homekit_hvac_mode in self.hc_homekit_to_hass:
                if self.char_target_heat_cool.value != homekit_hvac_mode:
                    self.char_target_heat_cool.set_value(homekit_hvac_mode)
            else:
                _LOGGER.error(
                    "Cannot map hvac target mode: %s to homekit as only %s modes are supported",
                    hvac_mode,
                    self.hc_homekit_to_hass,
                )

        # Set current operation mode for supported thermostats
        hvac_action = new_state.attributes.get(ATTR_HVAC_ACTION)
        if hvac_action:
            homekit_hvac_action = HC_HASS_TO_HOMEKIT_ACTION[hvac_action]
            if self.char_current_heat_cool.value != homekit_hvac_action:
                self.char_current_heat_cool.set_value(homekit_hvac_action)

        # Update current temperature
        current_temp = _get_current_temperature(new_state, self._unit)
        if current_temp is not None:
            if self.char_current_temp.value != current_temp:
                self.char_current_temp.set_value(current_temp)

        # Update current humidity
        if CHAR_CURRENT_HUMIDITY in self.chars:
            current_humdity = new_state.attributes.get(ATTR_CURRENT_HUMIDITY)
            if isinstance(current_humdity, (int, float)):
                if self.char_current_humidity.value != current_humdity:
                    self.char_current_humidity.set_value(current_humdity)

        # Update target humidity
        if CHAR_TARGET_HUMIDITY in self.chars:
            target_humdity = new_state.attributes.get(ATTR_HUMIDITY)
            if isinstance(target_humdity, (int, float)):
                if self.char_target_humidity.value != target_humdity:
                    self.char_target_humidity.set_value(target_humdity)

        # Update cooling threshold temperature if characteristic exists
        if self.char_cooling_thresh_temp:
            cooling_thresh = new_state.attributes.get(ATTR_TARGET_TEMP_HIGH)
            if isinstance(cooling_thresh, (int, float)):
                cooling_thresh = self._temperature_to_homekit(cooling_thresh)
                if self.char_heating_thresh_temp.value != cooling_thresh:
                    self.char_cooling_thresh_temp.set_value(cooling_thresh)

        # Update heating threshold temperature if characteristic exists
        if self.char_heating_thresh_temp:
            heating_thresh = new_state.attributes.get(ATTR_TARGET_TEMP_LOW)
            if isinstance(heating_thresh, (int, float)):
                heating_thresh = self._temperature_to_homekit(heating_thresh)
                if self.char_heating_thresh_temp.value != heating_thresh:
                    self.char_heating_thresh_temp.set_value(heating_thresh)

        # Update target temperature
        target_temp = _get_target_temperature(new_state, self._unit)
        if target_temp is None and features & SUPPORT_TARGET_TEMPERATURE_RANGE:
            # Homekit expects a target temperature
            # even if the device does not support it
            hc_hvac_mode = self.char_target_heat_cool.value
            if hc_hvac_mode == HC_HEAT_COOL_HEAT:
                temp_low = new_state.attributes.get(ATTR_TARGET_TEMP_LOW)
                if isinstance(temp_low, (int, float)):
                    target_temp = self._temperature_to_homekit(temp_low)
            elif hc_hvac_mode == HC_HEAT_COOL_COOL:
                temp_high = new_state.attributes.get(ATTR_TARGET_TEMP_HIGH)
                if isinstance(temp_high, (int, float)):
                    target_temp = self._temperature_to_homekit(temp_high)
        if target_temp and self.char_target_temp.value != target_temp:
            self.char_target_temp.set_value(target_temp)

        # Update display units
        if self._unit and self._unit in UNIT_HASS_TO_HOMEKIT:
            unit = UNIT_HASS_TO_HOMEKIT[self._unit]
            if self.char_display_units.value != unit:
                self.char_display_units.set_value(unit)


class Thermostat(Thermostat0):
    """Generate a Thermostat accessory for a climate."""

    def __init__(self, *args):
        super().__init__(*args)
        self._state = 0
        self._state_flag = False
        serv_fan = self.add_preload_service(SERV_FANV2)
        self.char_active = serv_fan.configure_char(
            CHAR_ACTIVE, value=0, setter_callback=self.set_state)

    def set_state(self, value):
        """Set state if call came from HomeKit."""
        _LOGGER.debug('%s: Set state to %d', self.entity_id, value)
        self._state_flag = True
        service = SERVICE_TURN_ON if value == 1 else SERVICE_TURN_OFF
        params = {ATTR_ENTITY_ID: self.entity_id}
        self.hass.services.call(DOMAIN_CLIMATE, service, params)

    def update_state(self, new_state):
        """Update thermostat state after state changed."""
        state = new_state.state
        if state in (STATE_ON, STATE_OFF):
            self._state = 1 if state == STATE_ON else 0
            if not self._state_flag and \
                    self.char_active.value != self._state:
                self.char_active.set_value(self._state)
            self._state_flag = False
        super().update_state(new_state)


@TYPES.register("WaterHeater")
class WaterHeater(HomeAccessory):
    """Generate a WaterHeater accessory for a water_heater."""

    def __init__(self, *args):
        """Initialize a WaterHeater accessory object."""
        super().__init__(*args, category=CATEGORY_THERMOSTAT)
        self._unit = self.hass.config.units.temperature_unit
        min_temp, max_temp = self.get_temperature_range()

        serv_thermostat = self.add_preload_service(SERV_THERMOSTAT)

        self.char_current_heat_cool = serv_thermostat.configure_char(
            CHAR_CURRENT_HEATING_COOLING, value=1
        )
        self.char_target_heat_cool = serv_thermostat.configure_char(
            CHAR_TARGET_HEATING_COOLING,
            value=1,
            setter_callback=self.set_heat_cool,
            valid_values=HC_HOMEKIT_VALID_MODES_WATER_HEATER,
        )

        self.char_current_temp = serv_thermostat.configure_char(
            CHAR_CURRENT_TEMPERATURE, value=50.0
        )
        self.char_target_temp = serv_thermostat.configure_char(
            CHAR_TARGET_TEMPERATURE,
            value=50.0,
            # We do not set PROP_MIN_STEP here and instead use the HomeKit
            # default of 0.1 in order to have enough precision to convert
            # temperature units and avoid setting to 73F will result in 74F
            properties={PROP_MIN_VALUE: min_temp, PROP_MAX_VALUE: max_temp},
            setter_callback=self.set_target_temperature,
        )

        self.char_display_units = serv_thermostat.configure_char(
            CHAR_TEMP_DISPLAY_UNITS, value=0
        )

        state = self.hass.states.get(self.entity_id)
        self.async_update_state(state)

    def get_temperature_range(self):
        """Return min and max temperature range."""
        return _get_temperature_range_from_state(
            self.hass.states.get(self.entity_id),
            self._unit,
            DEFAULT_MIN_TEMP_WATER_HEATER,
            DEFAULT_MAX_TEMP_WATER_HEATER,
        )

    def set_heat_cool(self, value):
        """Change operation mode to value if call came from HomeKit."""
        _LOGGER.debug("%s: Set heat-cool to %d", self.entity_id, value)
        hass_value = HC_HOMEKIT_TO_HASS[value]
        if hass_value != HVAC_MODE_HEAT:
            if self.char_target_heat_cool.value != 1:
                self.char_target_heat_cool.set_value(1)  # Heat

    def set_target_temperature(self, value):
        """Set target temperature to value if call came from HomeKit."""
        _LOGGER.debug("%s: Set target temperature to %.1f°C", self.entity_id, value)
        temperature = temperature_to_states(value, self._unit)
        params = {ATTR_ENTITY_ID: self.entity_id, ATTR_TEMPERATURE: temperature}
        self.call_service(
            DOMAIN_WATER_HEATER,
            SERVICE_SET_TEMPERATURE_WATER_HEATER,
            params,
            f"{temperature}{self._unit}",
        )

    @callback
    def async_update_state(self, new_state):
        """Update water_heater state after state change."""
        # Update current and target temperature
        target_temperature = _get_target_temperature(new_state, self._unit)
        if target_temperature is not None:
            if target_temperature != self.char_target_temp.value:
                self.char_target_temp.set_value(target_temperature)

        current_temperature = _get_current_temperature(new_state, self._unit)
        if current_temperature is not None:
            if current_temperature != self.char_current_temp.value:
                self.char_current_temp.set_value(current_temperature)

        # Update display units
        if self._unit and self._unit in UNIT_HASS_TO_HOMEKIT:
            unit = UNIT_HASS_TO_HOMEKIT[self._unit]
            if self.char_display_units.value != unit:
                self.char_display_units.set_value(unit)

        # Update target operation mode
        operation_mode = new_state.state
        if operation_mode and self.char_target_heat_cool.value != 1:
            self.char_target_heat_cool.set_value(1)  # Heat


def _get_temperature_range_from_state(state, unit, default_min, default_max):
    """Calculate the temperature range from a state."""
    min_temp = state.attributes.get(ATTR_MIN_TEMP)
    if min_temp:
        min_temp = round(temperature_to_homekit(min_temp, unit) * 2) / 2
    else:
        min_temp = default_min

    max_temp = state.attributes.get(ATTR_MAX_TEMP)
    if max_temp:
        max_temp = round(temperature_to_homekit(max_temp, unit) * 2) / 2
    else:
        max_temp = default_max

    # Homekit only supports 10-38, overwriting
    # the max to appears to work, but less than 0 causes
    # a crash on the home app
    min_temp = max(min_temp, 0)
    if min_temp > max_temp:
        max_temp = min_temp

    return min_temp, max_temp


def _get_target_temperature(state, unit):
    """Calculate the target temperature from a state."""
    target_temp = state.attributes.get(ATTR_TEMPERATURE)
    if isinstance(target_temp, (int, float)):
        return temperature_to_homekit(target_temp, unit)
    return None


def _get_current_temperature(state, unit):
    """Calculate the current temperature from a state."""
    target_temp = state.attributes.get(ATTR_CURRENT_TEMPERATURE)
    if isinstance(target_temp, (int, float)):
        return temperature_to_homekit(target_temp, unit)
    return None
