"""ONEp1 Energie Manager integration for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError

from .const import CHANNEL_PROPERTIES, CONF_API_KEY, DOMAIN
from .coordinator import ONEp1Coordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.NUMBER, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ONEp1 from a config entry."""
    coordinator = ONEp1Coordinator(hass, entry.data[CONF_API_KEY])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Komt er een dongel, accu, omvormer, fase of watermeter bij (of gaat er een weg), dan
    # herladen we de integratie zodat de entiteiten kloppen. Geen herstart van HA nodig.
    signature = coordinator.signature()
    reloading = False

    @callback
    def _check_devices():
        nonlocal reloading
        if reloading or not coordinator.last_update_success or not coordinator.data:
            return
        if coordinator.needs_reload(signature, coordinator.signature()):
            reloading = True
            _LOGGER.info("ONEp1: apparaten gewijzigd, integratie wordt herladen")
            hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))

    entry.async_on_unload(coordinator.async_add_listener(_check_devices))

    async def handle_set_channel(call: ServiceCall):
        """onep1.set_channel: uitgang aanpassen (standaard op de eerste ONEp1)."""
        channel = int(call.data.get("channel"))
        settings = {prop: call.data[prop] for prop in CHANNEL_PROPERTIES if prop in call.data}
        if not settings:
            _LOGGER.warning("No settings provided for set_channel service")
            return
        meter = call.data.get("meter")
        for coord in hass.data[DOMAIN].values():
            if not isinstance(coord, ONEp1Coordinator):
                continue
            code = str(meter) if meter else coord.first_meter_code()
            if code and coord.meter(code):
                await coord.async_set_channel(code, channel, settings)
                _LOGGER.info("Channel %d of %s updated: %s", channel, code, settings)
                return
        raise HomeAssistantError(f"Geen ONEp1 gevonden{' met koppelcode ' + str(meter) if meter else ''}")

    if not hass.services.has_service(DOMAIN, "set_channel"):
        hass.services.async_register(DOMAIN, "set_channel", handle_set_channel)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "set_channel")
    return unload_ok
