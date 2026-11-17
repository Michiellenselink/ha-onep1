"""Getalvelden: max vermogen per uitgang, vermogenslimiet solarONE, handmatig accuvermogen batteryONE."""

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfPower
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
            entities.append(ChannelMaxPower(coordinator, entry, m["pairing_code"], ch))
    for s in data.get("solarone") or []:
        entities.append(SolarPowerLimit(coordinator, entry, s["pairing_code"]))
    for b in data.get("batteryone") or []:
        entities.append(BatteryManualPower(coordinator, entry, b["pairing_code"]))
    async_add_entities(entities)


class ChannelMaxPower(ONEp1MeterEntity, NumberEntity):
    """Max vermogen van een uitgang (planningshint voor het algoritme, geen beveiliging)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = NumberDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_native_min_value = 0
    _attr_native_max_value = 25
    _attr_native_step = 0.1
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:flash"

    def __init__(self, coordinator, entry, code, channel):
        super().__init__(coordinator, entry, code, f"ch{channel}_max_power")
        self._channel = channel
        self._attr_name = f"Kanaal {channel} max vermogen"

    @property
    def native_value(self):
        chans = (self.meter or {}).get("channels") or []
        return chans[self._channel].get("maxPower") if self._channel < len(chans) else None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_channel(self._code, self._channel, {"maxPower": round(value, 1)})


class SolarPowerLimit(ONEp1SolarEntity, NumberEntity):
    """Vermogenslimiet in modus Handmatig (% van het omvormervermogen)."""

    _attr_name = "Vermogenslimiet"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:solar-power-variant"

    def __init__(self, coordinator, entry, code):
        super().__init__(coordinator, entry, code, "power_limit")

    @property
    def native_value(self):
        return (self.dev or {}).get("power_limit_percent")

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_solarone(self._code, {"power_limit_percent": round(value)})


class BatteryManualPower(ONEp1BatteryEntity, NumberEntity):
    """Vermogen in modus Handmatig: positief = ontladen, negatief = laden."""

    _attr_name = "Handmatig vermogen"
    _attr_device_class = NumberDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_native_step = 50
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:battery-charging"

    def __init__(self, coordinator, entry, code):
        super().__init__(coordinator, entry, code, "manual_w")

    @property
    def native_min_value(self):
        return -float((self.dev or {}).get("max_charge_w") or 10000)

    @property
    def native_max_value(self):
        return float((self.dev or {}).get("max_discharge_w") or 10000)

    @property
    def native_value(self):
        return (self.dev or {}).get("manual_w")

    @property
    def extra_state_attributes(self):
        return {"teken": "positief = ontladen, negatief = laden"}

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_batteryone(self._code, {"manual_w": round(value)})
