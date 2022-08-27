
from homeassistant.components.braviatv.media_player import BraviaTVMediaPlayer
from homeassistant.helpers import discovery
from . import async_add_bravia_entity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await async_add_bravia_entity(hass, config, async_add_entities, BraviaTVMediaPlayer)
    await discovery.async_load_platform(hass, 'remote', 'zhibravia', config, {})
