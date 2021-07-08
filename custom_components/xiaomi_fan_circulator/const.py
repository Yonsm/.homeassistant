"""Constants of the Mijia Circulator component."""

DEFAULT_NAME = "Xiaomi Circulating Fan"
DOMAIN = "xiaomi_fan_circulator"
DOMAINS = ["fan"]

CONF_MODEL = "model"
MODEL_FAN_FA1 = "zhimi.fan.fa1"
MODEL_FAN_FB1 = "zhimi.fan.fb1"
OPT_MODEL = {
    MODEL_FAN_FA1: "Xiaomi Fan Circulator (China)",
    MODEL_FAN_FB1: "Xiaomi Fan Circulator (Global)"
}

DEFAULT_RETRIES = 20
DATA_KEY = "fan.xiaomi_fan_circulator"

CONF_RETRIES = "retries"
