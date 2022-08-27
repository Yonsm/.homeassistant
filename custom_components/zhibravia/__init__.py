from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PIN
from homeassistant.config_entries import ConfigEntry, SOURCE_USER
from homeassistant.util import slugify


async def async_setup(hass, config):
    confs = config['zhibravia']
    for conf in confs:
        name = conf.get('name')
        unique_id = slugify(name)
        if hass.config_entries.async_get_entry(unique_id):
            continue

        host = conf[CONF_HOST]
        pin = conf.get(CONF_PIN, '0000')
        data = {
            CONF_HOST: host,
            CONF_MAC: conf.get(CONF_MAC) or await bravia_get_mac(hass, host, pin),
            CONF_PIN: pin
        }
        await hass.config_entries.async_add(ConfigEntry(1, 'braviatv', name, data, SOURCE_USER, unique_id=unique_id, entry_id=unique_id))
    return True


async def bravia_get_mac(hass, host, pin):
    from homeassistant.components.braviatv.const import CLIENTID_PREFIX, NICKNAME, ATTR_MAC
    from bravia_tv import BraviaRC
    device = BraviaRC(host)
    await hass.async_add_executor_job(device.connect, pin, CLIENTID_PREFIX, NICKNAME)
    if not await hass.async_add_executor_job(device.is_connected):
        return None

    info = await hass.async_add_executor_job(device.get_system_info)
    if not info:
        return None
    return info[ATTR_MAC]
