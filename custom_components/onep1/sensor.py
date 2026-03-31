"""Sensor platform for ONEp1."""

import logging
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ONEp1Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up ONEp1 sensors from a config entry."""
    coordinator: ONEp1Coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ONEp1PowerSensor(coordinator, entry, "consumed", "Verbruik"),
        ONEp1PowerSensor(coordinator, entry, "produced", "Teruglevering"),
        ONEp1EnergySensor(coordinator, entry, "consumed_total", "Verbruik Totaal"),
        ONEp1EnergySensor(coordinator, entry, "produced_total", "Teruglevering Totaal"),
        ONEp1GasSensor(coordinator, entry),
    ]

    # Always create 4 channel sensors with fixed names (user can rename in HA)
    device = None
    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data["devices"]
        if devices:
            device = devices[0]

    for idx in range(4):
        entities.append(
            ONEp1ChannelSensor(coordinator, entry, device, idx, f"Kanaal {idx}")
        )

    async_add_entities(entities)


class ONEp1PowerSensor(CoordinatorEntity, SensorEntity):
    """ONEp1 power sensor (consumed/produced)."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, sensor_type, name):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"ONEp1 {name}"
        self._attr_unique_id = f"onep1_{entry.entry_id}_{sensor_type}"

    @property
    def device_info(self):
        """Return device info."""
        device_id = None
        if self.coordinator.data and "devices" in self.coordinator.data:
            devices = self.coordinator.data["devices"]
            if devices:
                device_id = devices[0].get("deviceId")

        return {
            "identifiers": {(DOMAIN, device_id or self.coordinator.config_entry.entry_id)},
            "name": "ONEp1 Energie Manager",
            "manufacturer": "ONEev B.V.",
            "model": "ONEp1 Dongle",
            "configuration_url": "https://onep1.nl/dashboard.html",
            "sw_version": self.coordinator.data.get("devices", [{}])[0].get("firmwareVersion") if self.coordinator.data else None,
        }

    @property
    def native_value(self):
        """Return the state."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        devices = self.coordinator.data["devices"]
        if not devices:
            return None
        power = devices[0].get("power", {})
        return power.get(self._sensor_type, 0)


class ONEp1EnergySensor(CoordinatorEntity, SensorEntity):
    """ONEp1 energy sensor in kWh (for HA Energy dashboard)."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, sensor_type, name):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"ONEp1 {name}"
        self._attr_unique_id = f"onep1_{entry.entry_id}_{sensor_type}"

    @property
    def device_info(self):
        """Return device info."""
        device_id = None
        if self.coordinator.data and "devices" in self.coordinator.data:
            devices = self.coordinator.data["devices"]
            if devices:
                device_id = devices[0].get("deviceId")
        return {
            "identifiers": {(DOMAIN, device_id or self.coordinator.config_entry.entry_id)},
            "name": "ONEp1 Energie Manager",
            "manufacturer": "ONEev B.V.",
            "model": "ONEp1 Dongle",
            "configuration_url": "https://onep1.nl/dashboard.html",
        }

    @property
    def native_value(self):
        """Return the state in kWh."""
        if not self.coordinator.data or "energy" not in self.coordinator.data:
            return None
        energy = self.coordinator.data["energy"]
        return energy.get(self._sensor_type, 0)


class ONEp1GasSensor(CoordinatorEntity, SensorEntity):
    """ONEp1 gas sensor in m³ (for HA Energy dashboard)."""

    _attr_device_class = SensorDeviceClass.GAS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "ONEp1 Gas"
        self._attr_unique_id = f"onep1_{entry.entry_id}_gas"

    @property
    def device_info(self):
        """Return device info."""
        device_id = None
        if self.coordinator.data and "devices" in self.coordinator.data:
            devices = self.coordinator.data["devices"]
            if devices:
                device_id = devices[0].get("deviceId")
        return {
            "identifiers": {(DOMAIN, device_id or self.coordinator.config_entry.entry_id)},
            "name": "ONEp1 Energie Manager",
            "manufacturer": "ONEev B.V.",
            "model": "ONEp1 Dongle",
            "configuration_url": "https://onep1.nl/dashboard.html",
        }

    @property
    def native_value(self):
        """Return the state in m³."""
        if not self.coordinator.data or "energy" not in self.coordinator.data:
            return None
        energy = self.coordinator.data["energy"]
        return energy.get("gas", 0)


class ONEp1ChannelSensor(CoordinatorEntity, SensorEntity):
    """ONEp1 channel status sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, device, channel_index, channel_name):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device = device
        self._channel_index = channel_index
        self._attr_name = f"ONEp1 {channel_name}"
        self._attr_unique_id = f"onep1_{entry.entry_id}_ch{channel_index}"
        self._attr_icon = "mdi:flash"

    @property
    def device_info(self):
        """Return device info."""
        device_id = None
        if self.coordinator.data and "devices" in self.coordinator.data:
            devices = self.coordinator.data["devices"]
            if devices:
                device_id = devices[0].get("deviceId")

        return {
            "identifiers": {(DOMAIN, device_id or self.coordinator.config_entry.entry_id)},
            "name": "ONEp1 Energie Manager",
            "manufacturer": "ONEev B.V.",
            "model": "ONEp1 Dongle",
            "configuration_url": "https://onep1.nl/dashboard.html",
            "sw_version": self.coordinator.data.get("devices", [{}])[0].get("firmwareVersion") if self.coordinator.data else None,
        }

    @property
    def native_value(self):
        """Return channel status."""
        channel = self._get_channel()
        if not channel:
            return "unknown"
        if not channel.get("active", False):
            return "uit"
        return f"prio {channel.get('priority', '?')} | max {channel.get('maxPower', '?')} kW"

    @property
    def extra_state_attributes(self):
        """Return channel attributes."""
        channel = self._get_channel()
        if not channel:
            return {}
        return {
            "active": channel.get("active"),
            "priority": channel.get("priority"),
            "max_power_kw": channel.get("maxPower"),
            "reaction_time_s": channel.get("reactionTime"),
            "threshold_power_kw": channel.get("thresholdPower"),
            "is_battery": channel.get("isBattery"),
            "is_meter": channel.get("isMeter"),
            "economic_mode": channel.get("economicMode"),
        }

    def _get_channel(self):
        """Get channel data from coordinator."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        devices = self.coordinator.data["devices"]
        if not devices:
            return None
        channels = devices[0].get("channels", [])
        for ch in channels:
            if ch.get("index") == self._channel_index:
                return ch
        return None
