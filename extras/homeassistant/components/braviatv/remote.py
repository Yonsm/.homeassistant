"""Remote control support for Bravia TV."""

from homeassistant.components.remote import ATTR_NUM_REPEATS, RemoteEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_MANUFACTURER, DEFAULT_NAME, DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Bravia TV Remote from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    unique_id = config_entry.unique_id
    device_info = {
        "identifiers": {(DOMAIN, unique_id)},
        "name": DEFAULT_NAME,
        "manufacturer": ATTR_MANUFACTURER,
        "model": config_entry.title,
    }

    async_add_entities(
        [BraviaTVRemote(coordinator, device_info['model'], unique_id, device_info)]
    )


class BraviaTVRemote(CoordinatorEntity, RemoteEntity):
    """Representation of a Bravia TV Remote."""

    def __init__(self, coordinator, name, unique_id, device_info):
        """Initialize the entity."""

        self._attr_device_info = device_info
        self._attr_name = name
        self._attr_unique_id = unique_id

        super().__init__(coordinator)

    @property
    def is_on(self):
        """Return true if device is on."""
        return self.coordinator.is_on

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        await self.coordinator.async_turn_on()

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        await self.coordinator.async_turn_off()

    async def async_send_command(self, command, **kwargs):
        """Send a command to device."""
        repeats = kwargs[ATTR_NUM_REPEATS]
        await self.coordinator.async_send_command(command, repeats)
