from homeassistant.components.xiaomi_aqara import DOMAIN, CONF_HOST, CONF_MAC, CONF_SID, CONF_KEY, CONF_INTERFACE, CONF_PORT, CONF_PROTOCOL
from homeassistant.config_entries import ConfigEntry, SOURCE_USER
from homeassistant.util import slugify


async def async_setup(hass, config):
    conf = config.get('zhiaqara')
    name = conf.get('name') or conf[CONF_MAC]
    unique_id = slugify(name)
    if hass.config_entries.async_get_entry(unique_id):
        return True

    data = {
        CONF_HOST: conf[CONF_HOST],
        CONF_PORT: conf.get(CONF_PORT, 9898),
        CONF_MAC: conf[CONF_MAC],
        CONF_INTERFACE: conf.get(CONF_INTERFACE, 'any'),
        CONF_PROTOCOL: conf.get(CONF_PROTOCOL, '1.1.2'),
        CONF_KEY: conf[CONF_KEY],
        CONF_SID: conf[CONF_SID],
    }
    await hass.config_entries.async_add(ConfigEntry(1, DOMAIN, name, data, SOURCE_USER, unique_id=unique_id, entry_id=unique_id))
    return True
