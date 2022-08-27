from homeassistant.components.braviatv.remote import BraviaTVRemote
from . import async_add_bravia_entity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await async_add_bravia_entity(hass, config or discovery_info, async_add_entities, BraviaTVRemote)
