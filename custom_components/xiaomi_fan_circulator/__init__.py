""" Mijia Circulator """

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import (
    DOMAIN,
    DOMAINS
)

async def async_setup(hass: HomeAssistant, hass_config: dict):
    """Set up the Mijia Circulator component."""

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """ Update Optioins if available """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Support Mijia Circulator."""

    hass.data.setdefault(DOMAIN, {})

    # migrate data (also after first setup) to options
    if entry.data:
        hass.config_entries.async_update_entry(entry, data={},
                                               options=entry.data)

    # add update handler
    if not entry.update_listeners:
        entry.add_update_listener(async_update_options)

    # init setup for each supported domains
    for platform in DOMAINS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(
            entry, platform))

    return True
