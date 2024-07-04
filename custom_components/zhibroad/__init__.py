from json import load
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_MAC, CONF_TYPE, CONF_TIMEOUT
from homeassistant.config_entries import ConfigEntry, SOURCE_USER
from homeassistant.util import slugify
import broadlink as blk


async def async_setup(hass, config):
    confs = config['zhibroad']
    for conf in confs:
        name = conf[CONF_NAME]
        unique_id = slugify(name)
        if hass.config_entries.async_get_entry(unique_id):
            continue

        try:
            device = await hass.async_add_executor_job(blk.hello, conf[CONF_HOST], 80, 5)
            data = {
                CONF_HOST: device.host[0],
                CONF_MAC: device.mac.hex(),
                CONF_TYPE: device.devtype,
                CONF_TIMEOUT: device.timeout,
            }
            await hass.config_entries.async_add(ConfigEntry(
                version=1, 
                minor_version=0,
                options={},
                domain='broadlink',
                title=name,
                data=data, 
                source=SOURCE_USER, 
                unique_id=unique_id,
                entry_id=unique_id))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Could not find %s, %s", name, e)
    return True
