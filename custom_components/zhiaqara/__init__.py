from homeassistant.components.xiaomi_aqara import DOMAIN, CONF_HOST, CONF_MAC, CONF_SID, CONF_KEY, CONF_INTERFACE, CONF_PORT, CONF_PROTOCOL
from homeassistant.config_entries import ConfigEntry, SOURCE_USER
from homeassistant.helpers.device_registry import format_mac
from homeassistant.util import slugify
from xiaomi_gateway import XiaomiGatewayDiscovery


async def async_setup(hass, config):
    conf = config['zhiaqara']
    name = conf['name']
    unique_id = slugify(name)
    if hass.config_entries.async_get_entry(unique_id):
        return True

    interface = conf.get(CONF_INTERFACE, 'any')
    xiaomi = XiaomiGatewayDiscovery(interface)
    await hass.async_add_executor_job(xiaomi.discover_gateways)
    if len(xiaomi.gateways) == 0:
        return False

    gateway = list(xiaomi.gateways.values())[0]
    data = {
        CONF_HOST: gateway.ip_adress,
        CONF_PORT: gateway.port,
        CONF_MAC: format_mac(gateway.sid),
        CONF_INTERFACE: interface,
        CONF_PROTOCOL: gateway.proto,
        CONF_KEY: conf.get(CONF_KEY),
        CONF_SID: gateway.sid,
    }
    await hass.config_entries.async_add(ConfigEntry(1, DOMAIN, name, data, SOURCE_USER, unique_id=unique_id, entry_id=unique_id))
    return True
