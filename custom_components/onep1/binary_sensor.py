"""Binary sensors for ONEp1: online-status per dongel en de schakelaar "Besturing door Home Assistant"."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
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
        entities += [MeterOnline(coordinator, entry, m["pairing_code"]), MeterHaControl(coordinator, entry, m["pairing_code"])]
    for s in data.get("solarone") or []:
        entities.append(SolarOnline(coordinator, entry, s["pairing_code"]))
    for b in data.get("batteryone") or []:
        entities.append(BatteryOnline(coordinator, entry, b["pairing_code"]))
    async_add_entities(entities)


class _Online(BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Online"

    def _src(self):
        raise NotImplementedError

    @property
    def is_on(self):
        src = self._src()
        return bool(src and src.get("online"))


class MeterOnline(_Online, ONEp1MeterEntity):
    def __init__(self, coordinator, entry, code):
        super().__init__(coordinator, entry, code, "online")

    def _src(self):
        return self.meter


class SolarOnline(_Online, ONEp1SolarEntity):
    def __init__(self, coordinator, entry, code):
        super().__init__(coordinator, entry, code, "online")

    def _src(self):
        return self.dev


class BatteryOnline(_Online, ONEp1BatteryEntity):
    def __init__(self, coordinator, entry, code):
        super().__init__(coordinator, entry, code, "online")

    def _src(self):
        return self.dev


class MeterHaControl(ONEp1MeterEntity, BinarySensorEntity):
    """Staat "Besturing door Home Assistant" aan? Alleen dan werken de schakelaars en keuzes."""

    _attr_name = "Besturing door Home Assistant"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:home-assistant"

    def __init__(self, coordinator, entry, code):
        super().__init__(coordinator, entry, code, "ha_control")

    @property
    def is_on(self):
        m = self.meter
        return bool(m and m.get("ha_control"))
