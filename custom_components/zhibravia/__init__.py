
from homeassistant.util import slugify
from homeassistant.components.braviatv import BraviaTVCoordinator


async def async_add_bravia_entity(hass, config, async_add_entities, BraviaTVEntityType):
    name = config['name']
    entity_id = slugify(name)

    hass.data.setdefault('braviatv', {})
    if entity_id in hass.data['braviatv']:
        coordinator = hass.data['braviatv'][entity_id]
    else:
        coordinator = BraviaTVCoordinator(hass, config['host'], config['mac'], config['pin'], [])
        hass.data['braviatv'][entity_id] = coordinator
        await coordinator.async_config_entry_first_refresh()

    entity = BraviaTVEntityType(coordinator, entity_id, name)
    entity._attr_name = name
    async_add_entities([entity])
