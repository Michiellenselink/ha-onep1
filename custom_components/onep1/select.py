"""Keuzelijsten: prioriteit per uitgang en de modus van solarONE en batteryONE."""

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BATTERYONE_MODES, CHANNEL_COUNT, DOMAIN, SOLARONE_MODES
from .coordinator import ONEp1Coordinator
from .entity import ONEp1BatteryEntity, ONEp1MeterEntity, ONEp1SolarEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: ONEp1Coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    entities = []
    for m in data.get("meters") or []:
        for ch in range(len(m.get("channels") or [])):
            entities.append(ChannelPriority(coordinator, entry, m["pairing_code"], ch))
    for s in data.get("solarone") or []:
        entities.append(SolarMode(coordinator, entry, s["pairing_code"]))
    for b in data.get("batteryone") or []:
        entities.append(BatteryMode(coordinator, entry, b["pairing_code"]))
    async_add_entities(entities)


def _key_for(label, modes):
    for key, lab in modes.items():
        if lab == label:
            return key
    raise HomeAssistantError(f"Onbekende modus: {label}")


class ChannelPriority(ONEp1MeterEntity, SelectEntity):
    """Prioriteit van een uitgang (1 = eerst)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:order-numeric-ascending"
    _attr_options = [str(i) for i in range(1, CHANNEL_COUNT + 1)]

    def __init__(self, coordinator, entry, code, channel):
        super().__init__(coordinator, entry, code, f"ch{channel}_priority")
        self._channel = channel
        self._attr_name = f"Kanaal {channel} prioriteit"

    @property
    def current_option(self):
        chans = (self.meter or {}).get("channels") or []
        if self._channel >= len(chans):
            return None
        prio = chans[self._channel].get("priority")
        return str(prio) if prio is not None and str(prio) in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_channel(self._code, self._channel, {"priority": int(option)})


class SolarMode(ONEp1SolarEntity, SelectEntity):
    _attr_name = "Modus"
    _attr_icon = "mdi:tune-variant"
    _attr_options = list(SOLARONE_MODES.values())

    def __init__(self, coordinator, entry, code):
        super().__init__(coordinator, entry, code, "mode")

    @property
    def current_option(self):
        return SOLARONE_MODES.get((self.dev or {}).get("control_mode"))

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_solarone(self._code, {"control_mode": _key_for(option, SOLARONE_MODES)})


class BatteryMode(ONEp1BatteryEntity, SelectEntity):
    _attr_name = "Modus"
    _attr_icon = "mdi:tune-variant"
    _attr_options = list(BATTERYONE_MODES.values())

    def __init__(self, coordinator, entry, code):
        super().__init__(coordinator, entry, code, "mode")

    @property
    def current_option(self):
        return BATTERYONE_MODES.get((self.dev or {}).get("mode"))

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_batteryone(self._code, {"mode": _key_for(option, BATTERYONE_MODES)})
