"""
Support for MQTT switches with icon_template and original_state support.

"""
import logging

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.components.mqtt import (
    CONF_STATE_TOPIC, CONF_QOS, subscription)
from homeassistant.const import (
    CONF_OPTIMISTIC, CONF_VALUE_TEMPLATE, CONF_ICON_TEMPLATE)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import HomeAssistantType, ConfigType
from homeassistant.components.mqtt.switch import (MqttSwitch, PLATFORM_SCHEMA)

_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_ICON_TEMPLATE): cv.template,
})


async def async_setup_platform(hass: HomeAssistantType, config: ConfigType,
                               async_add_entities, discovery_info=None):
    """Set up MQTT switch through configuration.yaml."""
    async_add_entities([MqttSwitch2(hass, config, None, discovery_info)])
# pylint: disable=too-many-ancestors


class MqttSwitch2(MqttSwitch):
    """Representation of a switch that can be toggled using MQTT."""

    def __init__(self, hass, config, config_entry, discovery_data):
        """Initialize the MQTT switch."""
        super().__init__(hass, config, config_entry, discovery_data)
        self._attributes = None
        self._icon = None

    async def _subscribe_topics(self):
        """(Re)Subscribe to topics."""
        template = self._config.get(CONF_VALUE_TEMPLATE)
        if template is not None:
            template.hass = self.hass
        icon_template = self._config.get(CONF_ICON_TEMPLATE)
        if icon_template is not None:
            icon_template.hass = self.hass

        @callback
        def state_message_received(msg):
            """Handle new MQTT state messages."""
            payload = msg.payload
            if icon_template is not None:
                self._icon = icon_template.async_render_with_possible_json_value(
                    payload)

            if template is not None:
                self._attributes = {'original_state': payload}
                payload = template.async_render_with_possible_json_value(
                    payload)

            if payload == self._state_on:
                self._state = True
            elif payload == self._state_off:
                self._state = False

            self.async_schedule_update_ha_state()

        if self._config.get(CONF_STATE_TOPIC) is None:
            # Force into optimistic mode.
            self._optimistic = True
        else:
            self._sub_state = await subscription.async_subscribe_topics(
                self.hass, self._sub_state,
                {CONF_STATE_TOPIC:
                 {'topic': self._config.get(CONF_STATE_TOPIC),
                  'msg_callback': state_message_received,
                  'qos': self._config.get(CONF_QOS)}})

        if self._optimistic:
            last_state = await self.async_get_last_state()
            if last_state:
                self._state = last_state

    @property
    def icon(self):
        """Return the icon."""
        return self._icon

    @property
    def state_attributes(self):
        """Return attributes."""
        return self._attributes
