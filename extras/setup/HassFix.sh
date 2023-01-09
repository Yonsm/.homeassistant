#!/bin/sh
# Docker HASS=/usr/src/homeassistant/homeassistant
HASS=/usr/local/lib/python3.10/dist-packages/homeassistant

sed -i 's/_LOGGER.warning(CUSTOM_WARNING/#LOGGER.warning(CUSTOM_WARNING/' $HASS/loader.py
sed -i 's/minutes=30/days=30/' $HASS/auth/const.py
sed -i 's/ATTERY_MODELS:/ATTERY_MODELS and False:/' $HASS/components/xiaomi_aqara/sensor.py
sed -i 's/await hass.config_entries.async_forward_entry_setups/#wait hass.config_entries.async_forward_entry_setups/' $HASS/components/mobile_app/__init__.py

sed -i 's/Platform.BUTTON/#latform.BUTTON/' $HASS/components/braviatv/__init__.py
sed -i 's/f"{ATTR_MANUFACTURER} {model}"/model/' $HASS/components/braviatv/entity.py
#sed -i 's/await self.coordinator.async_turn_off()/await self.coordinator.async_turn_off(); await self.coordinator.async_turn_off()/' $HASS/components/braviatv/media_player.py

#sed -i 's/f"{device.name} Remote"/device.name/' $HASS/components/broadlink/remote.py
#sed -i 's/f"{device.name} Switch"/device.name/' $HASS/components/broadlink/switch.py
sed -i 's/"RM4PRO", "RM4MINI"/"RM4PRO", "RMPRO", "RM4MINI"/' $HASS/components/broadlink/sensor.py
