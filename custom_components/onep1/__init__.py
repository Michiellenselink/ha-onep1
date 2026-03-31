"""ONEp1 Energie Manager integration for Home Assistant."""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, CONF_API_KEY, CHANNEL_PROPERTIES
from .coordinator import ONEp1Coordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ONEp1 from a config entry."""
    coordinator = ONEp1Coordinator(hass, entry.data[CONF_API_KEY])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_set_channel(call: ServiceCall):
        """Handle the set_channel service call."""
        channel = call.data.get("channel")
        settings = {}
        for prop in CHANNEL_PROPERTIES:
            if prop in call.data:
                settings[prop] = call.data[prop]

        if not settings:
            _LOGGER.warning("No settings provided for set_channel service")
            return

        # Use first coordinator found
        for coord in hass.data[DOMAIN].values():
            if isinstance(coord, ONEp1Coordinator):
                result = await coord.async_set_channel(channel, settings)
                if result:
                    _LOGGER.info("Channel %d updated: %s", channel, settings)
                    await coord.async_request_refresh()
                return

    if not hass.services.has_service(DOMAIN, "set_channel"):
        hass.services.async_register(DOMAIN, "set_channel", handle_set_channel)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: ONEp1Coordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.async_shutdown()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove services if no more entries
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "set_channel")

    return unload_ok
