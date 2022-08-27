from homeassistant.const import CONF_PLATFORM
from homeassistant.components.mqtt.switch import MqttSwitch, subscription, CONF_QOS, CONF_ENCODING, CONF_STATE_TOPIC, PAYLOAD_NONE, PLATFORM_SCHEMA_MODERN
from homeassistant.const import CONF_VALUE_TEMPLATE, CONF_ICON_TEMPLATE
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


PLATFORM_SCHEMA = PLATFORM_SCHEMA_MODERN.extend({
    vol.Required(CONF_PLATFORM): cv.string,
    vol.Optional(CONF_ICON_TEMPLATE): cv.template,
})


async def async_setup_platform(hass, conf, async_add_entities, discovery_info=None):
    async_add_entities([ZhiMqttSwitch(hass, conf, None, discovery_info)])


class ZhiMqttSwitch(MqttSwitch):

    def __init__(self, hass, conf, config_entry, discovery_data):
        super().__init__(hass, conf, config_entry, discovery_data)
        self._attributes = None
        self._icon = None

    @property
    def unique_id(self):
        from homeassistant.util import slugify
        return self.__class__.__name__.lower() + '.' + slugify(self.name)

    def _setup_from_config(self, config):
        super()._setup_from_config(config)
        icon_template = self._config.get(CONF_ICON_TEMPLATE)
        if icon_template is not None:
            icon_template.hass = self.hass

    def _prepare_subscribe_topics(self):
        @callback
        def state_message_received(msg):
            if self._config.get(CONF_VALUE_TEMPLATE) is not None:
                self._attributes = {'original_state': msg.payload}
            icon_template = self._config.get(CONF_ICON_TEMPLATE)
            if icon_template is not None:
                self._icon = icon_template.async_render_with_possible_json_value(msg.payload)

            payload = self._value_template(msg.payload)
            if payload == self._state_on:
                self._state = True
            elif payload == self._state_off:
                self._state = False
            elif payload == PAYLOAD_NONE:
                self._state = None

            self.async_write_ha_state()

        if self._config.get(CONF_STATE_TOPIC) is None:
            # Force into optimistic mode.
            self._optimistic = True
        else:
            self._sub_state = subscription.async_prepare_subscribe_topics(
                self.hass,
                self._sub_state,
                {
                    CONF_STATE_TOPIC: {
                        "topic": self._config.get(CONF_STATE_TOPIC),
                        "msg_callback": state_message_received,
                        "qos": self._config[CONF_QOS],
                        "encoding": self._config[CONF_ENCODING] or None,
                    }
                },
            )

    @property
    def icon(self):
        return self._icon

    @property
    def state_attributes(self):
        return self._attributes
