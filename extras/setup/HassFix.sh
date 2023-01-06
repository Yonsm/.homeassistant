#!/bin/sh

sed -i 's/_LOGGER.warning(CUSTOM_WARNING/#LOGGER.warning(CUSTOM_WARNING/' /usr/src/homeassistant/homeassistant/loader.py
sed -i 's/minutes=30/days=30/' /usr/src/homeassistant/homeassistant/auth/const.py
sed -i 's/ATTERY_MODELS:/ATTERY_MODELS and False:/' /usr/src/homeassistant/homeassistant/components/xiaomi_aqara/sensor.py
sed -i 's/await hass.config_entries.async_forward_entry_setups/#wait hass.config_entries.async_forward_entry_setups/' /usr/src/homeassistant/homeassistant/components/mobile_app/__init__.py

sed -i 's/Platform.BUTTON/#latform.BUTTON/' /usr/src/homeassistant/homeassistant/components/braviatv/__init__.py
sed -i 's/f"{ATTR_MANUFACTURER} {model}"/model/' /usr/src/homeassistant/homeassistant/components/braviatv/entity.py
#sed -i 's/await self.coordinator.async_turn_off()/await self.coordinator.async_turn_off(); await self.coordinator.async_turn_off()/' /usr/src/homeassistant/homeassistant/components/braviatv/media_player.py

#sed -i 's/f"{device.name} Remote"/device.name/' /usr/src/homeassistant/homeassistant/components/broadlink/remote.py
#sed -i 's/f"{device.name} Switch"/device.name/' /usr/src/homeassistant/homeassistant/components/broadlink/switch.py
sed -i 's/"RM4PRO", "RM4MINI"/"RM4PRO", "RMPRO", "RM4MINI"/' /usr/src/homeassistant/homeassistant/components/broadlink/sensor.py
