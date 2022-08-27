from homeassistant.const import CONF_PLATFORM
from homeassistant.components.broadlink.device import BroadlinkDevice, DEFAULT_PORT, CONF_MAC, CONF_HOST, CONF_TYPE, AuthenticationError, NetworkTimeoutError, ConfigEntryNotReady,  BroadlinkException, get_update_manager
from homeassistant.components.broadlink import BroadlinkData
from homeassistant.components.broadlink.remote import DOMAIN, async_setup_entry
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import slugify

class FakeHass:
    pass
    

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    data = {
        'host': config['host'],
        'mac': config['mac'],
        'type': config['type'],
        'timeout': 5,
    }
    name = config['name']
    entry_id = slugify(name)
    entry = ConfigEntry(version=1, domain='broadlink', entry_id=entry_id, unique_id=entry_id, title=name, data=data, source='user')

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = BroadlinkData()
    if entry_id not in hass.data[DOMAIN].devices:
        if 1:
            device = BroadlinkDevice(hass, entry)
            #hass.data[DOMAIN].devices[entry_id] = device

            import broadlink as blk
            config = entry
            api = blk.gendevice(
                config.data[CONF_TYPE],
                (config.data[CONF_HOST], DEFAULT_PORT),
                bytes.fromhex(config.data[CONF_MAC]),
                name=config.title,
            )
            api.timeout = 5
            device.api = api

            try:
                device.fw_version = await device.hass.async_add_executor_job(device._get_firmware_version)
            except AuthenticationError:
                await device._async_handle_auth_error()
                return False
            except (NetworkTimeoutError, OSError) as err:
                raise ConfigEntryNotReady from err
            except BroadlinkException as err:
                return False

            device.authorized = True
            update_manager = get_update_manager(device)
            coordinator = update_manager.coordinator
            await coordinator.async_config_entry_first_refresh()

            device.update_manager = update_manager
            hass.data[DOMAIN].devices[config.entry_id] = device
            device.reset_jobs.append(config.add_update_listener(device.async_update))
        else:
            async def async_forward_entry_setups(config, _=None):
                pass
            fake = FakeHass()
            fake.async_add_executor_job = hass.async_add_executor_job
            fake.devices = {}
            fake.data = {DOMAIN: fake}
            fake.config_entries = fake
            fake.async_forward_entry_setups = async_forward_entry_setups

            device = BroadlinkDevice(fake, entry)
            await device.async_setup()
            device.hass = hass
            hass.data[DOMAIN].devices[entry_id] = device

    await async_setup_entry(hass, entry, async_add_entities)
