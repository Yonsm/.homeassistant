"""
Support for Xiaomi Mijia DC Frequency Conversion Circulating Fan.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/fan.xiaomi_miio/
"""
import asyncio
from functools import partial
import logging

import voluptuous as vol

from miio import Fan
from miio import Device, DeviceException

from homeassistant.components.fan import (
    FanEntity,
    PLATFORM_SCHEMA,
    SUPPORT_SET_SPEED,
    DOMAIN,
    SPEED_OFF,
    SUPPORT_OSCILLATE,
    SUPPORT_DIRECTION,
    ATTR_SPEED,
    ATTR_SPEED_LIST,
    ATTR_OSCILLATING,
    ATTR_DIRECTION,
)
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_TOKEN, ATTR_ENTITY_ID
from homeassistant.exceptions import PlatformNotReady
from homeassistant.config_entries import SOURCE_IMPORT
import homeassistant.helpers.config_validation as cv

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    DEFAULT_RETRIES,
    CONF_RETRIES,
    CONF_MODEL,
    MODEL_FAN_FA1,
    MODEL_FAN_FB1,
    DATA_KEY
)

_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MODEL): vol.In(
            [
                MODEL_FAN_FA1, MODEL_FAN_FB1,
            ]
        ),
        vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): cv.positive_int,
    }
)

ATTR_MODEL = "model"
ATTR_BRIGHTNESS = "brightness"

ATTR_TEMPERATURE = "temperature"
ATTR_HUMIDITY = "humidity"
ATTR_LED = "led"
ATTR_LED_BRIGHTNESS = "led_brightness"
ATTR_BUZZER = "buzzer"
ATTR_CHILD_LOCK = "child_lock"
ATTR_NATURAL_SPEED = "natural_speed"
ATTR_OSCILLATE = "oscillate"
ATTR_BATTERY = "battery"
ATTR_BATTERY_CHARGE = "battery_charge"
ATTR_BATTERY_STATE = "battery_state"
ATTR_AC_POWER = "ac_power"
ATTR_DELAY_OFF_COUNTDOWN = "delay_off_countdown"
ATTR_ANGLE = "angle"
ATTR_DIRECT_SPEED = "direct_speed"
ATTR_USE_TIME = "use_time"
ATTR_BUTTON_PRESSED = "button_pressed"
ATTR_RAW_SPEED = "raw_speed"
ATTR_MODE = "mode"

AVAILABLE_ATTRIBUTES_FAN = {
    ATTR_ANGLE: "angle",
    ATTR_RAW_SPEED: "speed",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_AC_POWER: "ac_power",
    ATTR_OSCILLATE: "oscillate",
    ATTR_DIRECT_SPEED: "direct_speed",
    ATTR_NATURAL_SPEED: "natural_speed",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_BUZZER: "buzzer",
    ATTR_LED_BRIGHTNESS: "led_brightness",
    ATTR_USE_TIME: "use_time",
    # Additional properties of version 2 and 3
    ATTR_TEMPERATURE: "temperature",
    ATTR_HUMIDITY: "humidity",
    ATTR_BATTERY: "battery",
    ATTR_BATTERY_CHARGE: "battery_charge",
    ATTR_BUTTON_PRESSED: "button_pressed",
    # Additional properties of version 2
    ATTR_LED: "led",
    ATTR_BATTERY_STATE: "battery_state",
}

AVAILABLE_ATTRIBUTES_FAN_FA1 = {
    ATTR_MODE: "mode",
    ATTR_OSCILLATING: "oscillate",
    ATTR_ANGLE: "angle",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_LED: "led",
    ATTR_BUZZER: "buzzer",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_RAW_SPEED: "speed",
    ATTR_DIRECTION: "direction"
}

FAN_SPEED_LEVEL1 = "Level 1"
FAN_SPEED_LEVEL2 = "Level 2"
FAN_SPEED_LEVEL3 = "Level 3"
FAN_SPEED_LEVEL4 = "Level 4"
FAN_SPEED_LEVEL5 = "Level 5"

FAN_SPEED_LIST = {
    SPEED_OFF: range(0, 1),
    FAN_SPEED_LEVEL1: range(1, 26),
    FAN_SPEED_LEVEL2: range(26, 51),
    FAN_SPEED_LEVEL3: range(51, 76),
    FAN_SPEED_LEVEL4: range(76, 101),
    FAN_SPEED_LEVEL5: range(101, 126),
}

FAN_SPEED_LIST_FA1 = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 2,
    FAN_SPEED_LEVEL3: 3,
    FAN_SPEED_LEVEL4: 4,
    FAN_SPEED_LEVEL5: 5,
}

FAN_SPEED_VALUES = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 35,
    FAN_SPEED_LEVEL3: 74,
    FAN_SPEED_LEVEL4: 100,
}

FAN_SPEED_VALUES_FA1 = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 2,
    FAN_SPEED_LEVEL3: 3,
    FAN_SPEED_LEVEL4: 4,
    FAN_SPEED_LEVEL5: 5,
}

SUCCESS = ["ok"]

FEATURE_SET_BUZZER = 1
FEATURE_SET_LED = 2
FEATURE_SET_CHILD_LOCK = 4
FEATURE_SET_LED_BRIGHTNESS = 8
FEATURE_SET_OSCILLATION_ANGLE = 16
FEATURE_SET_NATURAL_MODE = 32

FEATURE_FLAGS_GENERIC = FEATURE_SET_BUZZER | FEATURE_SET_CHILD_LOCK

FEATURE_FLAGS_FAN = (
    FEATURE_FLAGS_GENERIC
    | FEATURE_SET_LED_BRIGHTNESS
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_NATURAL_MODE
)

FEATURE_FLAGS_FAN_FA1 = (
    FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_NATURAL_MODE
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_LED
)

SERVICE_SET_BUZZER_ON = "xiaomi_miio_set_buzzer_on"
SERVICE_SET_BUZZER_OFF = "xiaomi_miio_set_buzzer_off"
SERVICE_SET_CHILD_LOCK_ON = "xiaomi_miio_set_child_lock_on"
SERVICE_SET_CHILD_LOCK_OFF = "xiaomi_miio_set_child_lock_off"
SERVICE_SET_LED_BRIGHTNESS = "xiaomi_miio_set_led_brightness"
SERVICE_SET_OSCILLATION_ANGLE = "xiaomi_miio_set_oscillation_angle"
SERVICE_SET_DELAY_OFF = "xiaomi_miio_set_delay_off"
SERVICE_SET_NATURAL_MODE_ON = "xiaomi_miio_set_natural_mode_on"
SERVICE_SET_NATURAL_MODE_OFF = "xiaomi_miio_set_natural_mode_off"
SERVICE_SET_HORIZONTAL_SWING_BACK = "xiaomi_miio_set_horizontal_swing_back"
SERVICE_SET_VERTICAL_SWING_BACK = "xiaomi_miio_set_vertical_swing_back"

AIRPURIFIER_SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_SCHEMA_LED_BRIGHTNESS = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=2))}
)

SERVICE_SCHEMA_OSCILLATION_ANGLE = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_ANGLE): vol.All(vol.Coerce(int), vol.In([30, 60, 90, 120, 140]))}
)

SERVICE_SCHEMA_DELAY_OFF = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_DELAY_OFF_COUNTDOWN):
        vol.All(vol.Coerce(int), vol.In([0, 60, 120, 180, 240, 300, 360, 420, 480]))}
)

SERVICE_TO_METHOD = {
    SERVICE_SET_BUZZER_ON: {"method": "async_set_buzzer_on"},
    SERVICE_SET_BUZZER_OFF: {"method": "async_set_buzzer_off"},
    SERVICE_SET_CHILD_LOCK_ON: {"method": "async_set_child_lock_on"},
    SERVICE_SET_CHILD_LOCK_OFF: {"method": "async_set_child_lock_off"},
    SERVICE_SET_LED_BRIGHTNESS: {
        "method": "async_set_led_brightness",
        "schema": SERVICE_SCHEMA_LED_BRIGHTNESS,
    },
    SERVICE_SET_OSCILLATION_ANGLE: {
        "method": "async_set_oscillation_angle",
        "schema": SERVICE_SCHEMA_OSCILLATION_ANGLE,
    },
    SERVICE_SET_DELAY_OFF: {
        "method": "async_set_delay_off",
        "schema": SERVICE_SCHEMA_DELAY_OFF,
    },
    SERVICE_SET_NATURAL_MODE_ON: {"method": "async_set_natural_mode_on"},
    SERVICE_SET_NATURAL_MODE_OFF: {"method": "async_set_natural_mode_off"},
    SERVICE_SET_HORIZONTAL_SWING_BACK: {"method": "async_set_horizontal_swing_back"},
    SERVICE_SET_VERTICAL_SWING_BACK: {"method": "async_set_vertical_swing_back"},
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Import Mijia Circulator configuration from YAML."""
    _LOGGER.warning(
        "Loading Mijia Circulator via platform setup is deprecated; Please remove it from your configuration"
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )


async def async_setup_entry(hass, config, async_add_devices, discovery_info=None):
    # pylint: disable=unused-argument, too-many-locals
    """Set up the miio fan device from config."""

    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    if config.data.get(CONF_HOST, None):
        host = config.data[CONF_HOST]
        token = config.data[CONF_TOKEN]
    else:
        host = config.options[CONF_HOST]
        token = config.options[CONF_TOKEN]

    model = config.options.get(CONF_MODEL)
    retries = config.options.get(CONF_RETRIES, DEFAULT_RETRIES)
    name = config.title

    _LOGGER.info("Initializing with host %s (token %s...)", host, token[:5])
    unique_id = None

    try:
        miio_device = Device(host, token)
        device_info = miio_device.info()
        if device_info.model:
            model = device_info.model
        unique_id = "{}-{}".format(model, device_info.mac_address)
        _LOGGER.info(
            "%s %s %s detected",
            model,
            device_info.firmware_version,
            device_info.hardware_version,
        )
    except DeviceException:
        raise PlatformNotReady

    if model in (MODEL_FAN_FA1, MODEL_FAN_FB1):

        if unique_id is None:
            unique_id = "{}-{}".format(model, host)
        fan = Fan(host, token, model=model)
        device = XiaomiFanFA1(name, fan, model, unique_id, retries)
    else:
        _LOGGER.error(
            "Unsupported device found! Please create an issue at "
            "https://github.com/tsunglung/xiaomi_fan_circulator/issues "
            "and provide the following data: %s",
            model,
        )
        return False

    hass.data[DATA_KEY][host] = device
    async_add_devices([device], update_before_add=True)

    async def async_service_handler(service):
        """Map services to methods on XiaomiFan."""
        method = SERVICE_TO_METHOD.get(service.service)
        params = {
            key: value for key, value in service.data.items() if key != ATTR_ENTITY_ID
        }
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [
                device
                for device in hass.data[DATA_KEY].values()
                if device.entity_id in entity_ids
            ]
        else:
            devices = hass.data[DATA_KEY].values()

        update_tasks = []
        for device in devices:
            if not hasattr(device, method["method"]):
                continue
            await getattr(device, method["method"])(**params)
            update_tasks.append(device.async_update_ha_state(True))

        if update_tasks:
            await asyncio.wait(update_tasks, loop=hass.loop)

    for service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[service].get(
            "schema", AIRPURIFIER_SERVICE_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, service, async_service_handler, schema=schema
        )


class XiaomiGenericDevice(FanEntity):
# pylint: disable=too-many-instance-attributes
    """Representation of a generic Xiaomi device."""

    def __init__(self, name, device, model, unique_id, retries):
        # pylint: disable=too-many-arguments
        """Initialize the generic Xiaomi device."""
        self._name = name
        self._device = device
        self._model = model
        self._unique_id = unique_id
        self._retry = 0
        self._retries = retries

        self._available = False
        self._state = None
        self._state_attrs = {ATTR_MODEL: self._model}
        self._device_features = FEATURE_FLAGS_GENERIC
        self._skip_update = False

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    @property
    def should_poll(self):
        """Poll the device."""
        return True

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state


    async def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a miio device command handling error messages."""

        try:
            result = await self.hass.async_add_job(partial(func, *args, **kwargs))

            _LOGGER.debug("Response received from miio device: %s", result)

            return result == SUCCESS
        except DeviceException as exc:
            _LOGGER.error(mask_error, exc)
            self._available = False
            return False

    async def async_turn_on(self, speed: str = None, **kwargs) -> None:
        # pylint: disable=unused-argument
        """Turn the device on."""
        result = await self._try_command(
            "Turning the miio device on failed.", self._device.on
        )
        if speed:
            result = await self.async_set_speed(speed)

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs) -> None:
        # pylint: disable=unused-argument
        """Turn the device off."""
        result = await self._try_command(
            "Turning the miio device off failed.", self._device.off
        )

        if result:
            self._state = False
            self._skip_update = True

    async def async_set_buzzer_on(self):
        """Turn the buzzer on."""
        if self._device_features & FEATURE_SET_BUZZER == 0:
            return

        await self._try_command(
            "Turning the buzzer of the miio device on failed.",
            self._device.set_buzzer,
            True,
        )

    async def async_set_buzzer_off(self):
        """Turn the buzzer off."""
        if self._device_features & FEATURE_SET_BUZZER == 0:
            return

        await self._try_command(
            "Turning the buzzer of the miio device off failed.",
            self._device.set_buzzer,
            False,
        )

    async def async_set_child_lock_on(self):
        """Turn the child lock on."""
        if self._device_features & FEATURE_SET_CHILD_LOCK == 0:
            return

        await self._try_command(
            "Turning the child lock of the miio device on failed.",
            self._device.set_child_lock,
            True,
        )

    async def async_set_child_lock_off(self):
        """Turn the child lock off."""
        if self._device_features & FEATURE_SET_CHILD_LOCK == 0:
            return

        await self._try_command(
            "Turning the child lock of the miio device off failed.",
            self._device.set_child_lock,
            False,
        )


class XiaomiFanFA1(XiaomiGenericDevice):
# pylint: disable=too-many-instance-attributes
    """Representation of a Xiaomi Pedestal Fan FA1."""

    def __init__(self, name, device, model, unique_id, retries):
        # pylint: disable=too-many-arguments
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries)

        self._device_features = FEATURE_FLAGS_FAN_FA1
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_FA1
        self._speed_list = list(FAN_SPEED_LIST_FA1)
        self._speed = None
        self._unique_id = unique_id
        self._oscillate = None
        self._natural_mode = False
        self._retry = retries
        self._state_attrs[ATTR_SPEED] = None
        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )
        self._did = None

    @property
    def supported_features(self) -> int:
        """Supported features."""
        return SUPPORT_SET_SPEED | SUPPORT_OSCILLATE | SUPPORT_DIRECTION | FEATURE_SET_NATURAL_MODE

    async def async_update(self):
        """Fetch state from the device."""

        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            if self._did is None:
                status = await self.hass.async_add_job(
                    self._device.raw_command,
                    "get_properties",
                    [{"piid": 3, "siid": 1, "did": self._did}]
                )
                if status[0]['code'] == 0:
                    self._did = status[0]['value']
                else:
                    self._did = self._unique_id

            status = await self.hass.async_add_job(
                self._device.raw_command,
                "get_properties",
                [{"piid": 1, "siid": 2, "did": self._did}]
            )
            _LOGGER.info("Got new status: %s", status)

            if status[0]['code'] == 0:
                self._state = status[0]['value']
                self._available = True
                status = await self.hass.async_add_job(
                    self._device.raw_command,
                    "get_properties",
                    [{"piid": 7, "siid": 2, "did": self._did}]
                )
                self._natural_mode = status[0]['value'] == 0
                self._state_attrs[ATTR_MODE] = status[0]['value']

                status = await self.hass.async_add_job(
                    self._device.raw_command,
                    "get_properties",
                    [{"piid": 3, "siid": 2, "did": self._did}]
                )
                self._oscillate = status[0]['value']
                self._state_attrs[ATTR_OSCILLATING] = self._oscillate

                status = await self.hass.async_add_job(
                    self._device.raw_command,
                    "get_properties",
                    [{"piid": 4, "siid": 2, "did": self._did}]
                )
                self._state_attrs[ATTR_DIRECTION] = status[0]['value']

                status = await self.hass.async_add_job(
                    self._device.raw_command,
                    "get_properties",
                    [{"piid": 5, "siid": 2, "did": self._did}]
                )
                self._state_attrs[ATTR_ANGLE] = status[0]['value']

                status = await self.hass.async_add_job(
                    self._device.raw_command,
                    "get_properties",
                    [{"piid": 10, "siid": 2, "did": self._did}]
                )
                self._state_attrs[ATTR_LED] = status[0]['value']

                status = await self.hass.async_add_job(
                    self._device.raw_command,
                    "get_properties",
                    [{"piid": 11, "siid": 2, "did": self._did}]
                )
                self._state_attrs[ATTR_BUZZER] = status[0]['value']

                status = await self.hass.async_add_job(
                    self._device.raw_command,
                    "get_properties",
                    [{"piid": 1, "siid": 6, "did": self._did}]
                )
                self._state_attrs[ATTR_CHILD_LOCK] = status[0]['value']

                status = await self.hass.async_add_job(
                    self._device.raw_command,
                    "get_properties",
                    [{"piid": 2, "siid": 5, "did": self._did}]
                )
                self._state_attrs[ATTR_DELAY_OFF_COUNTDOWN] = status[0]['value']

                status = await self.hass.async_add_job(
                    self._device.raw_command,
                    "get_properties",
                    [{"piid": 2, "siid": 2, "did": self._did}]
                )

                self._state_attrs[ATTR_NATURAL_SPEED] = status[0]['value']
                self._state_attrs[ATTR_RAW_SPEED] = status[0]['value']
                for level, value in FAN_SPEED_LIST_FA1.items():
                    if status[0]['value'] == value:
                        self._speed = level
                        self._state_attrs[ATTR_SPEED] = level
                        break

            else:
                self._available = False

            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "Got exception while fetching the state: %s , _retry=%s",
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "Got exception while fetching the state: %s , _retry=%s",
                    ex,
                    self._retry,
                )

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return self._speed_list

    @property
    def speed(self):
        """Return the current speed."""
        return self._speed

    async def async_turn_on(self, speed: str = None, **kwargs) -> None:
        """Turn the device on."""
        result = await self._try_command(
            "Turning the miio device on failed.",
            self._device.send,
            "set_properties",
            [{"piid": 1, "siid": 2, "did": self._did, "value": True}]
        )
        if speed:
            result = await self.async_set_speed(speed)

        if result:
            self._state = True
            self._skip_update = True


    async def async_turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        result = await self._try_command(
            "Turning the miio device off failed.",
            self._device.send,
            "set_properties",
            [{"piid": 1, "siid": 2, "did": self._did, "value": False}]
        )

        if result:
            self._state = False
            self._skip_update = True

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if self.supported_features & SUPPORT_SET_SPEED == 0:
            return

        if speed.isdigit():
            speed = int(speed)

        if speed in [SPEED_OFF, 0]:
            await self.async_turn_off()
            return

        # Map speed level to speed
        if speed in FAN_SPEED_VALUES_FA1.keys():
            speed = FAN_SPEED_VALUES_FA1[speed]

        await self._try_command(
            "Setting fan speed of the miio device failed.",
            self._device.send,
            "set_properties",
            [{"piid": 2, "siid": 2, "did": self._did, "value": speed}]
        )

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        if oscillating:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.send,
                "set_properties",
                [{"piid": 3, "siid": 2, "did": self._did, "value": True}]
            )
        else:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.send,
                "set_properties",
                [{"piid": 3, "siid": 2, "did": self._did, "value": False}]
            )

    async def async_set_oscillation_angle(self, angle: int) -> None:
        """Set oscillation angle."""
        if self._device_features & FEATURE_SET_OSCILLATION_ANGLE == 0:
            return

        await self._try_command(
            "Setting angle of the miio device failed.",
                self._device.send,
                "set_properties",
                [{"piid": 5, "siid": 2, "did": self._did, "value": angle}]
        )

    async def async_set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""

        if direction in ["forward", "right"]:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.send,
                "set_properties",
                [{"piid": 4, "siid": 2, "did": self._did, "value": True}]
            )
        else:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.send,
                "set_properties",
                [{"piid": 4, "siid": 2, "did": self._did, "value": False}]
            )

    async def async_set_led_brightness(self, brightness: int = 2):
        """Set the led brightness."""
        if self._device_features & FEATURE_SET_LED_BRIGHTNESS == 0:
            return

        await self._try_command(
            "Setting the led brightness of the miio device failed.",
                self._device.send,
                "set_properties",
                [{"piid": 10, "siid": 2, "did": self._did, "value": brightness}]
        )

    async def async_set_natural_mode_on(self):
        """Turn the natural mode on."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Turning on natural mode of the miio device failed.",
            self._device.send,
            "set_properties",
            [{"piid": 7, "siid": 2, "did": self._did, "value": 0}]
        )

    async def async_set_natural_mode_off(self):
        """Turn the natural mode off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Turning on natural mode of the miio device failed.",
            self._device.send,
            "set_properties",
            [{"piid": 7, "siid": 2, "did": self._did, "value": 1}]
        )

    async def async_set_delay_off(self, delay_off_countdown: int) -> None:
        """Set scheduled off timer in minutes"""

        await self._try_command(
            "Setting delay off miio device failed.", self._device.delay_off,
            self._device.send,
            "set_properties",
            [{"piid": 2, "siid": 5, "did": self._did, "value": delay_off_countdown}]
        )

    async def async_set_child_lock_on(self):
        """Turn the child lock on."""
        if self._device_features & FEATURE_SET_CHILD_LOCK == 0:
            return

        await self._try_command(
            "Turning the child lock of the miio device on failed.",
            self._device.send,
            "set_properties",
            [{"piid": 1, "siid": 6, "did": self._did, "value": True}]
        )

    async def async_set_child_lock_off(self):
        """Turn the child lock off."""
        if self._device_features & FEATURE_SET_CHILD_LOCK == 0:
            return

        await self._try_command(
            "Turning the child lock of the miio device off failed.",
            self._device.send,
            "set_properties",
            [{"piid": 1, "siid": 6, "did": self._did, "value": False}]
        )

    async def async_set_horizontal_swing_back(self):
        """Turn the natural mode on."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Turning on natural mode of the miio device failed.",
            self._device.send,
            "set_properties",
            [{"piid": 4, "siid": 5, "did": self._did, "value": True}]
        )

    async def async_set_vertical_swing_back(self):
        """Turn the natural mode on."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Turning on natural mode of the miio device failed.",
            self._device.send,
            "set_properties",
            [{"piid": 4, "siid": 5, "did": self._did, "value": True}]
        )
