"""Gedeelde basis voor ONEp1-entiteiten: één HA-apparaat per dongel."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONFIG_URL, DOMAIN, MANUFACTURER
from .coordinator import ONEp1Coordinator


class ONEp1MeterEntity(CoordinatorEntity[ONEp1Coordinator]):
    """Entiteit van een ONEp1 (P1-meter met 4 uitgangen)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ONEp1Coordinator, entry, code: str, key: str, legacy_unique_id: str | None = None):
        super().__init__(coordinator)
        self._code = code
        self._entry = entry
        # De eerste ONEp1 houdt de unique_ids van versie 1.x, zodat geschiedenis en dashboards blijven.
        self._attr_unique_id = legacy_unique_id or f"onep1_{entry.entry_id}_{code}_{key}"

    @property
    def meter(self):
        return self.coordinator.meter(self._code)

    @property
    def is_first(self):
        return self.coordinator.first_meter_code() == self._code

    @property
    def available(self):
        return super().available and self.meter is not None

    @property
    def device_info(self) -> DeviceInfo:
        m = self.meter or {}
        device_id = m.get("device_id") or self._entry.entry_id
        return DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name="ONEp1 Energie Manager" if self.is_first else f"ONEp1 Energie Manager ({self._code})",
            manufacturer=MANUFACTURER,
            model="ONEp1 Dongle",
            sw_version=m.get("firmware_version"),
            configuration_url=CONFIG_URL,
        )


class ONEp1SolarEntity(CoordinatorEntity[ONEp1Coordinator]):
    """Entiteit van een solarONE (omvormerbesturing)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ONEp1Coordinator, entry, code: str, key: str):
        super().__init__(coordinator)
        self._code = code
        self._attr_unique_id = f"onep1_{entry.entry_id}_solarone_{code}_{key}"

    @property
    def dev(self):
        return self.coordinator.solarone(self._code)

    @property
    def available(self):
        return super().available and self.dev is not None

    @property
    def device_info(self) -> DeviceInfo:
        d = self.dev or {}
        name = d.get("name") or self._code
        return DeviceInfo(
            identifiers={(DOMAIN, f"solarone_{self._code}")},
            name=f"solarONE {name}",
            manufacturer=MANUFACTURER,
            model="solarONE",
            sw_version=d.get("firmware_version"),
            configuration_url=CONFIG_URL,
        )


class ONEp1BatteryEntity(CoordinatorEntity[ONEp1Coordinator]):
    """Entiteit van een batteryONE (thuisaccubesturing)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ONEp1Coordinator, entry, code: str, key: str):
        super().__init__(coordinator)
        self._code = code
        self._attr_unique_id = f"onep1_{entry.entry_id}_batteryone_{code}_{key}"

    @property
    def dev(self):
        return self.coordinator.batteryone(self._code)

    @property
    def available(self):
        return super().available and self.dev is not None

    @property
    def device_info(self) -> DeviceInfo:
        d = self.dev or {}
        name = d.get("name") or self._code
        return DeviceInfo(
            identifiers={(DOMAIN, f"batteryone_{self._code}")},
            name=f"batteryONE {name}",
            manufacturer=MANUFACTURER,
            model="batteryONE",
            sw_version=d.get("firmware_version"),
            configuration_url=CONFIG_URL,
        )
