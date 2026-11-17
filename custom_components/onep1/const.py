"""Constants for ONEp1 integration."""

import os

DOMAIN = "onep1"
CONF_API_KEY = "api_key"
# ONEP1_API_BASE alleen voor ontwikkelen/testen tegen een lokale server.
API_BASE_URL = os.environ.get("ONEP1_API_BASE", "https://onep1.nl/api/ha").rstrip("/")
SCAN_INTERVAL_SECONDS = 10

MANUFACTURER = "ONEev B.V."
CONFIG_URL = "https://onep1.nl/dashboard.html"
CHANNEL_COUNT = 4

# Channel properties that can be updated (service onep1.set_channel)
CHANNEL_PROPERTIES = [
    "active", "priority", "maxPower", "reactionTime",
    "thresholdPower", "consumptionThreshold",
    "isBattery", "isMeter", "economicMode", "name"
]

# Modi zoals de server ze kent → leesbare naam in Home Assistant
SOLARONE_MODES = {
    "manual": "Handmatig",
    "zero_export": "Nul op de meter",
    "price": "Energieprijs",
    "negative_price": "Beperken bij negatieve prijs",
}
BATTERYONE_MODES = {
    "manual": "Handmatig",
    "zero_meter": "Nul op de meter",
    "price": "Energieprijs",
    "smart": "Slim (voorspellend)",
}

# Waarom de besturing doet wat hij doet (applied_reason) → leesbare tekst
REASONS = {
    "control_disabled": "Besturing uit",
    "battery_control_disabled": "Besturing uit",
    "manual": "Handmatig",
    "zero_export": "Nul op de meter",
    "zero_export_no_data": "Nul op de meter: geen meterdata",
    "zero_meter": "Nul op de meter",
    "zero_meter_no_data": "Nul op de meter: geen meterdata",
    "no_batteries": "Geen accu ingesteld",
    "unknown_mode": "Onbekende modus",
    "battery_first": "Eerst de accu laden",
    "price": "Energieprijs",
    "price_no_data": "Energieprijs: geen prijsdata",
    "price_charge": "Energieprijs: laden",
    "price_discharge": "Energieprijs: ontladen",
    "price_discharge_no_data": "Energieprijs: geen meterdata",
    "price_neutral": "Energieprijs: wachten",
    "negative_price": "Negatieve prijs: beperken",
    "negative_price_no_data": "Negatieve prijs: geen prijsdata",
    "negative_price_not_negative": "Prijs niet negatief: niet beperken",
    "negative_price_self_managed": "Leverancier regelt zelf",
    "negative_price_zero_export": "Negatieve prijs: nul op de meter",
    "negative_price_zero_export_no_data": "Negatieve prijs: geen meterdata",
    "smart_charge": "Slim: laden van het net",
    "smart_charge_plan": "Slim: laden volgens plan",
    "smart_export": "Slim: terugleveren",
    "smart_export_plan": "Slim: terugleveren volgens plan",
    "smart_self": "Slim: eigen verbruik",
    "smart_hold": "Slim: vasthouden",
    "smart_discharge_only": "Slim: alleen ontladen",
    "smart_idle": "Slim: rust",
    "smart_idle_no_data": "Slim: geen meterdata",
    "smart_no_data": "Slim: geen data",
    "smart_fallback": "Slim: nog geen plan (nul op de meter)",
}
