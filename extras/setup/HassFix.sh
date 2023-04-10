#!/bin/sh
cd /usr/src/homeassistant/homeassistant
cd /usr/lib/python3.10/site-packages/homeassistant

sed -i 's/_LOGGER.warning(CUSTOM_WARNING/#LOGGER.warning(CUSTOM_WARNING/' loader.py
sed -i 's/minutes=30/days=30/' auth/const.py
sed -i 's/ATTERY_MODELS:/ATTERY_MODELS and False:/' components/xiaomi_aqara/sensor.py
sed -i 's/await hass.config_entries.async_forward_entry_setups/#wait hass.config_entries.async_forward_entry_setups/' components/mobile_app/__init__.py

sed -i 's/Platform.BUTTON/#latform.BUTTON/' components/braviatv/__init__.py
sed -i 's/f"{ATTR_MANUFACTURER} {model}"/model/' components/braviatv/entity.py

sed -i 's/"RM4PRO", "RM4MINI"/"RM4PRO", "RMPRO", "RM4MINI"/' components/broadlink/sensor.py

sed -i 's/await hass.config_entries.async_forward_entry_setups/#wait hass.config_entries.async_forward_entry_setups/' components/sun/__init__.py
sed -i 's/await hass.config_entries.async_unload_platforms/True or await hass.config_entries.async_unload_platforms/' components/sun/__init__.py

grep 'CONF_ICON_TEMPLATE,' components/mqtt/switch.py || sed -i 's/CONF_VALUE_TEMPLATE,/CONF_VALUE_TEMPLATE, CONF_ICON_TEMPLATE,/' components/mqtt/switch.py
grep 'CONF_ICON_TEMPLATE)' components/mqtt/switch.py || sed -i 's/cv.template,/cv.template, vol.Optional(CONF_ICON_TEMPLATE): cv.template,/'  components/mqtt/switch.py
grep '"original_state": m' components/mqtt/switch.py || sed -i 's/payload = self._value_template/if CONF_VALUE_TEMPLATE in self._config: self._attr_state_attributes = {"original_state": msg.payload}\n            if CONF_ICON_TEMPLATE in self._config: self._attr_icon = self._config[CONF_ICON_TEMPLATE].async_render_with_possible_json_value(msg.payload)\n            payload = self._value_template/'  components/mqtt/switch.py
grep 'state_attributes(s,' components/mqtt/switch.py || sed -i 's/def _prepare_subscribe_topics/@property\n    def state_attributes(self): return self._attr_state_attributes if hasattr(self, "_attr_state_attributes") else None\n\n    def _prepare_subscribe_topics/' components/mqtt/switch.py
