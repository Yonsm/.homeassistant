"""Legacy device tracker classes."""
import asyncio
from datetime import timedelta
import hashlib
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Sequence

import attr
import voluptuous as vol

from homeassistant import util
from homeassistant.components import zone
from homeassistant.config import async_log_exception, load_yaml_config_file
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_GPS_ACCURACY,
    ATTR_ICON,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_NAME,
    CONF_ICON,
    CONF_MAC,
    CONF_NAME,
    DEVICE_DEFAULT_NAME,
    STATE_HOME,
    STATE_NOT_HOME,
)
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_per_platform, discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_registry import async_get_registry
from homeassistant.helpers.event import (
    async_track_time_interval,
    async_track_utc_time_change,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, GPSType, HomeAssistantType
from homeassistant.setup import async_prepare_setup_platform
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import dump

from .const import (
    ATTR_ATTRIBUTES,
    ATTR_BATTERY,
    ATTR_CONSIDER_HOME,
    ATTR_DEV_ID,
    ATTR_GPS,
    ATTR_HOST_NAME,
    ATTR_LOCATION_NAME,
    ATTR_MAC,
    ATTR_SOURCE_TYPE,
    CONF_CONSIDER_HOME,
    CONF_NEW_DEVICE_DEFAULTS,
    CONF_SCAN_INTERVAL,
    CONF_TRACK_NEW,
    DEFAULT_CONSIDER_HOME,
    DEFAULT_TRACK_NEW,
    DOMAIN,
    LOGGER,
    PLATFORM_TYPE_LEGACY,
    SCAN_INTERVAL,
    SOURCE_TYPE_BLUETOOTH,
    SOURCE_TYPE_BLUETOOTH_LE,
    SOURCE_TYPE_GPS,
    SOURCE_TYPE_ROUTER,
)

SERVICE_SEE = "see"

SOURCE_TYPES = (
    SOURCE_TYPE_GPS,
    SOURCE_TYPE_ROUTER,
    SOURCE_TYPE_BLUETOOTH,
    SOURCE_TYPE_BLUETOOTH_LE,
)

NEW_DEVICE_DEFAULTS_SCHEMA = vol.Any(
    None,
    vol.Schema({vol.Optional(CONF_TRACK_NEW, default=DEFAULT_TRACK_NEW): cv.boolean}),
)
PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_SCAN_INTERVAL): cv.time_period,
        vol.Optional(CONF_TRACK_NEW): cv.boolean,
        vol.Optional(CONF_CONSIDER_HOME, default=DEFAULT_CONSIDER_HOME): vol.All(
            cv.time_period, cv.positive_timedelta
        ),
        vol.Optional(CONF_NEW_DEVICE_DEFAULTS, default={}): NEW_DEVICE_DEFAULTS_SCHEMA,
    }
)
PLATFORM_SCHEMA_BASE = cv.PLATFORM_SCHEMA_BASE.extend(PLATFORM_SCHEMA.schema)

SERVICE_SEE_PAYLOAD_SCHEMA = vol.Schema(
    vol.All(
        cv.has_at_least_one_key(ATTR_MAC, ATTR_DEV_ID),
        {
            ATTR_MAC: cv.string,
            ATTR_DEV_ID: cv.string,
            ATTR_HOST_NAME: cv.string,
            ATTR_LOCATION_NAME: cv.string,
            ATTR_GPS: cv.gps,
            ATTR_GPS_ACCURACY: cv.positive_int,
            ATTR_BATTERY: cv.positive_int,
            ATTR_ATTRIBUTES: dict,
            ATTR_SOURCE_TYPE: vol.In(SOURCE_TYPES),
            ATTR_CONSIDER_HOME: cv.time_period,
            # Temp workaround for iOS app introduced in 0.65
            vol.Optional("battery_status"): str,
            vol.Optional("hostname"): str,
        },
    )
)

YAML_DEVICES = "known_devices.yaml"
EVENT_NEW_DEVICE = "device_tracker_new_device"


def see(
    hass: HomeAssistantType,
    mac: str = None,
    dev_id: str = None,
    host_name: str = None,
    location_name: str = None,
    gps: GPSType = None,
    gps_accuracy=None,
    battery: int = None,
    attributes: dict = None,
):
    """Call service to notify you see device."""
    data = {
        key: value
        for key, value in (
            (ATTR_MAC, mac),
            (ATTR_DEV_ID, dev_id),
            (ATTR_HOST_NAME, host_name),
            (ATTR_LOCATION_NAME, location_name),
            (ATTR_GPS, gps),
            (ATTR_GPS_ACCURACY, gps_accuracy),
            (ATTR_BATTERY, battery),
        )
        if value is not None
    }
    if attributes:
        data[ATTR_ATTRIBUTES] = attributes
    hass.services.call(DOMAIN, SERVICE_SEE, data)


async def async_setup_integration(hass: HomeAssistantType, config: ConfigType) -> None:
    """Set up the legacy integration."""
    tracker = await get_tracker(hass, config)

    legacy_platforms = await async_extract_config(hass, config)

    setup_tasks = [
        legacy_platform.async_setup_legacy(hass, tracker)
        for legacy_platform in legacy_platforms
    ]

    if setup_tasks:
        await asyncio.wait(setup_tasks)

    async def async_platform_discovered(p_type, info):
        """Load a platform."""
        platform = await async_create_platform_type(hass, config, p_type, {})

        if platform is None or platform.type != PLATFORM_TYPE_LEGACY:
            return

        await platform.async_setup_legacy(hass, tracker, info)

    discovery.async_listen_platform(hass, DOMAIN, async_platform_discovered)

    # Clean up stale devices
    async_track_utc_time_change(
        hass, tracker.async_update_stale, second=range(0, 60, 5)
    )

    async def async_see_service(call):
        """Service to see a device."""
        # Temp workaround for iOS, introduced in 0.65
        data = dict(call.data)
        data.pop("hostname", None)
        data.pop("battery_status", None)
        await tracker.async_see(**data)

    hass.services.async_register(
        DOMAIN, SERVICE_SEE, async_see_service, SERVICE_SEE_PAYLOAD_SCHEMA
    )

    # restore
    await tracker.async_setup_tracked_device()


@attr.s
class DeviceTrackerPlatform:
    """Class to hold platform information."""

    LEGACY_SETUP = (
        "async_get_scanner",
        "get_scanner",
        "async_setup_scanner",
        "setup_scanner",
    )

    name: str = attr.ib()
    platform: ModuleType = attr.ib()
    config: Dict = attr.ib()

    @property
    def type(self):
        """Return platform type."""
        for methods, platform_type in ((self.LEGACY_SETUP, PLATFORM_TYPE_LEGACY),):
            for meth in methods:
                if hasattr(self.platform, meth):
                    return platform_type

        return None

    async def async_setup_legacy(self, hass, tracker, discovery_info=None):
        """Set up a legacy platform."""
        LOGGER.info("Setting up %s.%s", DOMAIN, self.type)
        try:
            scanner = None
            setup = None
            if hasattr(self.platform, "async_get_scanner"):
                scanner = await self.platform.async_get_scanner(
                    hass, {DOMAIN: self.config}
                )
            elif hasattr(self.platform, "get_scanner"):
                scanner = await hass.async_add_executor_job(
                    self.platform.get_scanner, hass, {DOMAIN: self.config}
                )
            elif hasattr(self.platform, "async_setup_scanner"):
                setup = await self.platform.async_setup_scanner(
                    hass, self.config, tracker.async_see, discovery_info
                )
            elif hasattr(self.platform, "setup_scanner"):
                setup = await hass.async_add_executor_job(
                    self.platform.setup_scanner,
                    hass,
                    self.config,
                    tracker.see,
                    discovery_info,
                )
            else:
                raise HomeAssistantError("Invalid legacy device_tracker platform.")

            if scanner:
                async_setup_scanner_platform(
                    hass, self.config, scanner, tracker.async_see, self.type
                )
                return

            if not setup:
                LOGGER.error("Error setting up platform %s", self.type)
                return

        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Error setting up platform %s", self.type)


async def async_extract_config(hass, config):
    """Extract device tracker config and split between legacy and modern."""
    legacy = []

    for platform in await asyncio.gather(
        *(
            async_create_platform_type(hass, config, p_type, p_config)
            for p_type, p_config in config_per_platform(config, DOMAIN)
        )
    ):
        if platform is None:
            continue

        if platform.type == PLATFORM_TYPE_LEGACY:
            legacy.append(platform)
        else:
            raise ValueError(
                f"Unable to determine type for {platform.name}: {platform.type}"
            )

    return legacy


async def async_create_platform_type(
    hass, config, p_type, p_config
) -> Optional[DeviceTrackerPlatform]:
    """Determine type of platform."""
    platform = await async_prepare_setup_platform(hass, config, DOMAIN, p_type)

    if platform is None:
        return None

    return DeviceTrackerPlatform(p_type, platform, p_config)


@callback
def async_setup_scanner_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    scanner: Any,
    async_see_device: Callable,
    platform: str,
):
    """Set up the connect scanner-based platform to device tracker.

    This method must be run in the event loop.
    """
    interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
    update_lock = asyncio.Lock()
    scanner.hass = hass

    # Initial scan of each mac we also tell about host name for config
    seen: Any = set()

    async def async_device_tracker_scan(now: dt_util.dt.datetime):
        """Handle interval matches."""
        if update_lock.locked():
            LOGGER.warning(
                "Updating device list from %s took longer than the scheduled "
                "scan interval %s",
                platform,
                interval,
            )
            return

        async with update_lock:
            found_devices = await scanner.async_scan_devices()

        for mac in found_devices:
            if mac in seen:
                host_name = None
            else:
                host_name = await scanner.async_get_device_name(mac)
                seen.add(mac)

            try:
                extra_attributes = await scanner.async_get_extra_attributes(mac)
            except NotImplementedError:
                extra_attributes = {}

            kwargs = {
                "mac": mac,
                "host_name": host_name,
                "source_type": SOURCE_TYPE_ROUTER,
                "attributes": {
                    "scanner": scanner.__class__.__name__,
                    **extra_attributes,
                },
            }

            zone_home = hass.states.get(hass.components.zone.ENTITY_ID_HOME)
            if zone_home:
                kwargs["gps"] = [
                    zone_home.attributes[ATTR_LATITUDE],
                    zone_home.attributes[ATTR_LONGITUDE],
                ]
                kwargs["gps_accuracy"] = 0

            hass.async_create_task(async_see_device(**kwargs))

    async_track_time_interval(hass, async_device_tracker_scan, interval)
    hass.async_create_task(async_device_tracker_scan(None))


async def get_tracker(hass, config):
    """Create a tracker."""
    yaml_path = hass.config.path(YAML_DEVICES)

    conf = config.get(DOMAIN, [])
    conf = conf[0] if conf else {}
    consider_home = conf.get(CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME)

    defaults = conf.get(CONF_NEW_DEVICE_DEFAULTS, {})
    track_new = conf.get(CONF_TRACK_NEW)
    if track_new is None:
        track_new = defaults.get(CONF_TRACK_NEW, DEFAULT_TRACK_NEW)

    devices = await async_load_config(yaml_path, hass, consider_home)
    tracker = DeviceTracker(hass, consider_home, track_new, defaults, devices)
    return tracker


class DeviceTracker:
    """Representation of a device tracker."""

    def __init__(
        self,
        hass: HomeAssistantType,
        consider_home: timedelta,
        track_new: bool,
        defaults: dict,
        devices: Sequence,
    ) -> None:
        """Initialize a device tracker."""
        self.hass = hass
        self.devices = {dev.dev_id: dev for dev in devices}
        self.mac_to_dev = {dev.mac: dev for dev in devices if dev.mac}
        self.consider_home = consider_home
        self.track_new = (
            track_new
            if track_new is not None
            else defaults.get(CONF_TRACK_NEW, DEFAULT_TRACK_NEW)
        )
        self.defaults = defaults
        self._is_updating = asyncio.Lock()

        for dev in devices:
            if self.devices[dev.dev_id] is not dev:
                LOGGER.warning("Duplicate device IDs detected %s", dev.dev_id)
            if dev.mac and self.mac_to_dev[dev.mac] is not dev:
                LOGGER.warning("Duplicate device MAC addresses detected %s", dev.mac)

    def see(
        self,
        mac: str = None,
        dev_id: str = None,
        host_name: str = None,
        location_name: str = None,
        gps: GPSType = None,
        gps_accuracy: int = None,
        battery: int = None,
        attributes: dict = None,
        source_type: str = SOURCE_TYPE_GPS,
        picture: str = None,
        icon: str = None,
        consider_home: timedelta = None,
    ):
        """Notify the device tracker that you see a device."""
        self.hass.add_job(
            self.async_see(
                mac,
                dev_id,
                host_name,
                location_name,
                gps,
                gps_accuracy,
                battery,
                attributes,
                source_type,
                picture,
                icon,
                consider_home,
            )
        )

    async def async_see(
        self,
        mac: str = None,
        dev_id: str = None,
        host_name: str = None,
        location_name: str = None,
        gps: GPSType = None,
        gps_accuracy: int = None,
        battery: int = None,
        attributes: dict = None,
        source_type: str = SOURCE_TYPE_GPS,
        picture: str = None,
        icon: str = None,
        consider_home: timedelta = None,
    ):
        """Notify the device tracker that you see a device.

        This method is a coroutine.
        """
        registry = await async_get_registry(self.hass)
        if mac is None and dev_id is None:
            raise HomeAssistantError("Neither mac or device id passed in")
        if mac is not None:
            mac = str(mac).upper()
            device = self.mac_to_dev.get(mac)
            if not device:
                dev_id = util.slugify(host_name or "") or util.slugify(mac)
        else:
            dev_id = cv.slug(str(dev_id).lower())
            device = self.devices.get(dev_id)

        if device:
            await device.async_seen(
                host_name,
                location_name,
                gps,
                gps_accuracy,
                battery,
                attributes,
                source_type,
                consider_home,
            )
            if device.track:
                device.async_write_ha_state()
            return

        # Guard from calling see on entity registry entities.
        entity_id = f"{DOMAIN}.{dev_id}"
        if registry.async_is_registered(entity_id):
            LOGGER.error(
                "The see service is not supported for this entity %s", entity_id
            )
            return

        # If no device can be found, create it
        dev_id = util.ensure_unique_string(dev_id, self.devices.keys())
        device = Device(
            self.hass,
            consider_home or self.consider_home,
            self.track_new,
            dev_id,
            mac,
            picture=picture,
            icon=icon,
        )
        self.devices[dev_id] = device
        if mac is not None:
            self.mac_to_dev[mac] = device

        await device.async_seen(
            host_name,
            location_name,
            gps,
            gps_accuracy,
            battery,
            attributes,
            source_type,
        )

        if device.track:
            device.async_write_ha_state()

        self.hass.bus.async_fire(
            EVENT_NEW_DEVICE,
            {
                ATTR_ENTITY_ID: device.entity_id,
                ATTR_HOST_NAME: device.host_name,
                ATTR_MAC: device.mac,
            },
        )

        # update known_devices.yaml
        self.hass.async_create_task(
            self.async_update_config(
                self.hass.config.path(YAML_DEVICES), dev_id, device
            )
        )

    async def async_update_config(self, path, dev_id, device):
        """Add device to YAML configuration file.

        This method is a coroutine.
        """
        async with self._is_updating:
            await self.hass.async_add_executor_job(
                update_config, self.hass.config.path(YAML_DEVICES), dev_id, device
            )

    @callback
    def async_update_stale(self, now: dt_util.dt.datetime):
        """Update stale devices.

        This method must be run in the event loop.
        """
        for device in self.devices.values():
            if (device.track and device.last_update_home) and device.stale(now):
                self.hass.async_create_task(device.async_update_ha_state(True))

    async def async_setup_tracked_device(self):
        """Set up all not exists tracked devices.

        This method is a coroutine.
        """

        async def async_init_single_device(dev):
            """Init a single device_tracker entity."""
            await dev.async_added_to_hass()
            dev.async_write_ha_state()

        tasks = []
        for device in self.devices.values():
            if device.track and not device.last_seen:
                tasks.append(
                    self.hass.async_create_task(async_init_single_device(device))
                )

        if tasks:
            await asyncio.wait(tasks)


class Device(RestoreEntity):
    """Represent a tracked device."""

    host_name: str = None
    location_name: str = None
    gps: GPSType = None
    gps_accuracy: int = 0
    last_seen: dt_util.dt.datetime = None
    consider_home: dt_util.dt.timedelta = None
    battery: int = None
    attributes: dict = None
    icon: str = None

    # Track if the last update of this device was HOME.
    last_update_home = False
    _state = STATE_NOT_HOME

    def __init__(
        self,
        hass: HomeAssistantType,
        consider_home: timedelta,
        track: bool,
        dev_id: str,
        mac: str,
        name: str = None,
        picture: str = None,
        gravatar: str = None,
        icon: str = None,
    ) -> None:
        """Initialize a device."""
        self.hass = hass
        self.entity_id = f"{DOMAIN}.{dev_id}"

        # Timedelta object how long we consider a device home if it is not
        # detected anymore.
        self.consider_home = consider_home

        # Device ID
        self.dev_id = dev_id
        self.mac = mac

        # If we should track this device
        self.track = track

        # Configured name
        self.config_name = name

        # Configured picture
        if gravatar is not None:
            self.config_picture = get_gravatar_for_email(gravatar)
        else:
            self.config_picture = picture

        self.icon = icon

        self.source_type = None

        self._attributes = {}

    @property
    def name(self):
        """Return the name of the entity."""
        return self.config_name or self.host_name or self.dev_id or DEVICE_DEFAULT_NAME

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def entity_picture(self):
        """Return the picture of the device."""
        return self.config_picture

    @property
    def state_attributes(self):
        """Return the device state attributes."""
        attributes = {ATTR_SOURCE_TYPE: self.source_type}

        if self.gps:
            attributes[ATTR_LATITUDE] = self.gps[0]
            attributes[ATTR_LONGITUDE] = self.gps[1]
            attributes[ATTR_GPS_ACCURACY] = self.gps_accuracy

        if self.battery:
            attributes[ATTR_BATTERY] = self.battery

        return attributes

    @property
    def device_state_attributes(self):
        """Return device state attributes."""
        return self._attributes

    async def async_seen(
        self,
        host_name: str = None,
        location_name: str = None,
        gps: GPSType = None,
        gps_accuracy=0,
        battery: int = None,
        attributes: dict = None,
        source_type: str = SOURCE_TYPE_GPS,
        consider_home: timedelta = None,
    ):
        """Mark the device as seen."""
        self.source_type = source_type
        self.last_seen = dt_util.utcnow()
        self.host_name = host_name or self.host_name
        self.location_name = location_name
        self.consider_home = consider_home or self.consider_home

        if battery:
            self.battery = battery
        if attributes:
            self._attributes.update(attributes)

        self.gps = None

        if gps is not None:
            try:
                self.gps = float(gps[0]), float(gps[1])
                self.gps_accuracy = gps_accuracy or 0
            except (ValueError, TypeError, IndexError):
                self.gps = None
                self.gps_accuracy = 0
                LOGGER.warning("Could not parse gps value for %s: %s", self.dev_id, gps)

        await self.async_update()

    def stale(self, now: dt_util.dt.datetime = None):
        """Return if device state is stale.

        Async friendly.
        """
        return (
            self.last_seen is None
            or (now or dt_util.utcnow()) - self.last_seen > self.consider_home
        )

    def mark_stale(self):
        """Mark the device state as stale."""
        self._state = STATE_NOT_HOME
        self.gps = None
        self.last_update_home = False

    async def async_update(self):
        """Update state of entity.

        This method is a coroutine.
        """
        if not self.last_seen:
            return
        if self.location_name:
            self._state = self.location_name
        elif self.gps is not None and self.source_type == SOURCE_TYPE_GPS:
            zone_state = zone.async_active_zone(
                self.hass, self.gps[0], self.gps[1], self.gps_accuracy
            )
            if zone_state is None:
                self._state = STATE_NOT_HOME
            elif zone_state.entity_id == zone.ENTITY_ID_HOME:
                self._state = STATE_HOME
            else:
                self._state = zone_state.name
        elif self.stale():
            self.mark_stale()
        else:
            self._state = STATE_HOME
            self.last_update_home = True

    async def async_added_to_hass(self):
        """Add an entity."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not state:
            return
        self._state = state.state
        self.last_update_home = state.state == STATE_HOME
        self.last_seen = dt_util.utcnow()

        for attribute, var in (
            (ATTR_SOURCE_TYPE, "source_type"),
            (ATTR_GPS_ACCURACY, "gps_accuracy"),
            (ATTR_BATTERY, "battery"),
        ):
            if attribute in state.attributes:
                setattr(self, var, state.attributes[attribute])

        if ATTR_LONGITUDE in state.attributes:
            self.gps = (
                state.attributes[ATTR_LATITUDE],
                state.attributes[ATTR_LONGITUDE],
            )


class DeviceScanner:
    """Device scanner object."""

    hass: HomeAssistantType = None

    def scan_devices(self) -> List[str]:
        """Scan for devices."""
        raise NotImplementedError()

    async def async_scan_devices(self) -> Any:
        """Scan for devices."""
        return await self.hass.async_add_executor_job(self.scan_devices)

    def get_device_name(self, device: str) -> str:
        """Get the name of a device."""
        raise NotImplementedError()

    async def async_get_device_name(self, device: str) -> Any:
        """Get the name of a device."""
        return await self.hass.async_add_executor_job(self.get_device_name, device)

    def get_extra_attributes(self, device: str) -> dict:
        """Get the extra attributes of a device."""
        raise NotImplementedError()

    async def async_get_extra_attributes(self, device: str) -> Any:
        """Get the extra attributes of a device."""
        return await self.hass.async_add_executor_job(self.get_extra_attributes, device)


async def async_load_config(
    path: str, hass: HomeAssistantType, consider_home: timedelta
):
    """Load devices from YAML configuration file.

    This method is a coroutine.
    """
    dev_schema = vol.Schema(
        {
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_ICON, default=None): vol.Any(None, cv.icon),
            vol.Optional("track", default=False): cv.boolean,
            vol.Optional(CONF_MAC, default=None): vol.Any(
                None, vol.All(cv.string, vol.Upper)
            ),
            vol.Optional("gravatar", default=None): vol.Any(None, cv.string),
            vol.Optional("picture", default=None): vol.Any(None, cv.string),
            vol.Optional(CONF_CONSIDER_HOME, default=consider_home): vol.All(
                cv.time_period, cv.positive_timedelta
            ),
        }
    )
    result = []
    try:
        devices = await hass.async_add_executor_job(load_yaml_config_file, path)
    except HomeAssistantError as err:
        LOGGER.error("Unable to load %s: %s", path, str(err))
        return []
    except FileNotFoundError:
        return []

    for dev_id, device in devices.items():
        # Deprecated option. We just ignore it to avoid breaking change
        device.pop("vendor", None)
        device.pop("hide_if_away", None)
        try:
            device = dev_schema(device)
            device["dev_id"] = cv.slugify(dev_id)
        except vol.Invalid as exp:
            async_log_exception(exp, dev_id, devices, hass)
        else:
            result.append(Device(hass, **device))
    return result


def update_config(path: str, dev_id: str, device: Device):
    """Add device to YAML configuration file."""
    return
    with open(path, "a") as out:
        device = {
            device.dev_id: {
                ATTR_NAME: device.name,
                ATTR_MAC: device.mac,
                ATTR_ICON: device.icon,
                "picture": device.config_picture,
                "track": device.track,
            }
        }
        out.write("\n")
        out.write(dump(device))


def get_gravatar_for_email(email: str):
    """Return an 80px Gravatar for the given email address.

    Async friendly.
    """

    return (
        f"https://www.gravatar.com/avatar/"
        f"{hashlib.md5(email.encode('utf-8').lower()).hexdigest()}.jpg?s=80&d=wavatar"
    )
