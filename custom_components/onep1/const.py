"""Constants for ONEp1 integration."""

DOMAIN = "onep1"
CONF_API_KEY = "api_key"
API_BASE_URL = "https://onep1.nl/api/ha"
SCAN_INTERVAL_SECONDS = 10

# Sensor types
SENSOR_CONSUMED = "consumed"
SENSOR_PRODUCED = "produced"
SENSOR_NET = "net"

# Channel properties that can be updated
CHANNEL_PROPERTIES = [
    "active", "priority", "maxPower", "reactionTime",
    "thresholdPower", "consumptionThreshold",
    "isBattery", "isMeter", "economicMode", "name"
]
