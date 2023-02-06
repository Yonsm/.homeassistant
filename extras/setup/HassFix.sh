#!/bin/sh
# Docker HASS=/usr/src/homeassistant/homeassistant
cd /usr/lib/python3.10/site-packages/homeassistant

sed -i 's/_LOGGER.warning(CUSTOM_WARNING/#LOGGER.warning(CUSTOM_WARNING/' loader.py
sed -i 's/minutes=30/days=30/' auth/const.py
sed -i 's/ATTERY_MODELS:/ATTERY_MODELS and False:/' components/xiaomi_aqara/sensor.py
sed -i 's/await hass.config_entries.async_forward_entry_setups/#wait hass.config_entries.async_forward_entry_setups/' components/mobile_app/__init__.py

sed -i 's/Platform.BUTTON/#latform.BUTTON/' components/braviatv/__init__.py
sed -i 's/f"{ATTR_MANUFACTURER} {model}"/model/' components/braviatv/entity.py
#sed -i 's/await self.coordinator.async_turn_off()/await self.coordinator.async_turn_off(); await self.coordinator.async_turn_off()/' components/braviatv/media_player.py

#sed -i 's/f"{device.name} Remote"/device.name/' components/broadlink/remote.py
#sed -i 's/f"{device.name} Switch"/device.name/' components/broadlink/switch.py
sed -i 's/"RM4PRO", "RM4MINI"/"RM4PRO", "RMPRO", "RM4MINI"/' components/broadlink/sensor.py
