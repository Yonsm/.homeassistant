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
        await hass.config_entries.async_add(ConfigEntry(
            version=1, 
            minor_version=0,
            options={},
            domain='braviatv', 
            title=name, 
            data=data, 
            source=SOURCE_USER, 
            unique_id=unique_id, 
            entry_id=unique_id))
    return True


async def bravia_get_mac(hass, host, pin):
    from aiohttp import CookieJar
    from pybravia import BraviaClient
    from homeassistant.components.braviatv.const import ATTR_MAC
    from homeassistant.helpers.aiohttp_client import async_create_clientsession
    session = async_create_clientsession(hass, cookie_jar=CookieJar(unsafe=True, quote_cookie=False),)
    client = BraviaClient(host=host, session=session)
    await client.connect(psk=pin)
    await client.set_wol_mode(True)
    info = await client.get_system_info()
    # info = await hass.async_add_executor_job(client.get_system_info)
    if not info:
        return None
    return info[ATTR_MAC]
