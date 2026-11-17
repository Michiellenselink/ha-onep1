"""Schakelaars: uitgang aan/uit, economisch verbruik, besturing van solarONE en batteryONE."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ONEp1Coordinator
from .entity import ONEp1BatteryEntity, ONEp1MeterEntity, ONEp1SolarEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: ONEp1Coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    entities = []
    for m in data.get("meters") or []:
        for ch in range(len(m.get("channels") or [])):
            entities += [
                ChannelSwitch(coordinator, entry, m["pairing_code"], ch, "active", f"Kanaal {ch} aan", "mdi:power-socket-eu"),
                ChannelSwitch(coordinator, entry, m["pairing_code"], ch, "economicMode", f"Kanaal {ch} economisch verbruik", "mdi:cash-clock"),
            ]
    for s in data.get("solarone") or []:
        entities.append(SolarControlSwitch(coordinator, entry, s["pairing_code"]))
    for b in data.get("batteryone") or []:
        entities.append(BatteryControlSwitch(coordinator, entry, b["pairing_code"]))
    async_add_entities(entities)


class ChannelSwitch(ONEp1MeterEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry, code, channel, field, name, icon):
        super().__init__(coordinator, entry, code, f"ch{channel}_{field}")
        self._channel = channel
        self._field = field
        self._attr_name = name
        self._attr_icon = icon

    @property
    def is_on(self):
        chans = (self.meter or {}).get("channels") or []
        return bool(chans[self._channel].get(self._field)) if self._channel < len(chans) else None

    @property
    def extra_state_attributes(self):
        chans = (self.meter or {}).get("channels") or []
        return {"kanaalnaam": chans[self._channel].get("name")} if self._channel < len(chans) else None

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_channel(self._code, self._channel, {self._field: True})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_channel(self._code, self._channel, {self._field: False})


class SolarControlSwitch(ONEp1SolarEntity, SwitchEntity):
    _attr_name = "Besturing"
    _attr_icon = "mdi:solar-power"

    def __init__(self, coordinator, entry, code):
        super().__init__(coordinator, entry, code, "control_enabled")

    @property
    def is_on(self):
        return bool((self.dev or {}).get("control_enabled"))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_solarone(self._code, {"control_enabled": True})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_solarone(self._code, {"control_enabled": False})


class BatteryControlSwitch(ONEp1BatteryEntity, SwitchEntity):
    _attr_name = "Besturing"
    _attr_icon = "mdi:home-battery"

    def __init__(self, coordinator, entry, code):
        super().__init__(coordinator, entry, code, "control_enabled")

    @property
    def is_on(self):
        return bool((self.dev or {}).get("control_enabled"))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_batteryone(self._code, {"control_enabled": True})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_batteryone(self._code, {"control_enabled": False})
