"""Sensor platform for ONEp1."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, REASONS
from .coordinator import ONEp1Coordinator
from .entity import ONEp1BatteryEntity, ONEp1MeterEntity, ONEp1SolarEntity

PRICE_UNIT = "EUR/kWh"


def _get(d, *path):
    for p in path:
        if d is None:
            return None
        d = d[p] if isinstance(d, list) and isinstance(p, int) and p < len(d) else (d.get(p) if isinstance(d, dict) else None)
    return d


def _power(dc=SensorDeviceClass.POWER, unit=UnitOfPower.KILO_WATT):
    return {"device_class": dc, "state_class": SensorStateClass.MEASUREMENT, "unit": unit}


def _energy():
    return {"device_class": SensorDeviceClass.ENERGY, "state_class": SensorStateClass.TOTAL_INCREASING, "unit": UnitOfEnergy.KILO_WATT_HOUR}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: ONEp1Coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    entities = []

    for idx, m in enumerate(data.get("meters") or []):
        code = m["pairing_code"]
        first = idx == 0
        legacy = (lambda key: f"onep1_{entry.entry_id}_{key}") if first else (lambda key: None)
        energy = m.get("energy") or {}

        def meter(key, name, value, spec, legacy_name=False, category=None, attrs=None, _code=code, _legacy=legacy):
            return ONEp1MeterSensor(coordinator, entry, _code, key, name, value, spec,
                                    _legacy(key) if legacy_name else None, category, attrs)

        entities += [
            meter("consumed", "ONEp1 Verbruik", lambda m: _get(m, "power", "consumed_kw"), _power(), True),
            meter("produced", "ONEp1 Teruglevering", lambda m: _get(m, "power", "produced_kw"), _power(), True),
            meter("consumed_total", "ONEp1 Verbruik Totaal", lambda m: _get(m, "energy", "consumed_total"), _energy(), True),
            meter("produced_total", "ONEp1 Teruglevering Totaal", lambda m: _get(m, "energy", "produced_total"), _energy(), True),
            meter("net", "Netto vermogen", lambda m: _get(m, "power", "net_kw"), _power()),
            meter("consumed_t1", "Verbruik T1 (dal)", lambda m: _get(m, "energy", "consumed_t1"), _energy()),
            meter("consumed_t2", "Verbruik T2 (normaal)", lambda m: _get(m, "energy", "consumed_t2"), _energy()),
            meter("produced_t1", "Teruglevering T1 (dal)", lambda m: _get(m, "energy", "produced_t1"), _energy()),
            meter("produced_t2", "Teruglevering T2 (normaal)", lambda m: _get(m, "energy", "produced_t2"), _energy()),
        ]
        # Gas: de eerste ONEp1 had hem altijd (1.x); bij een extra ONEp1 alleen als er een gasmeter is.
        if first or energy.get("gas") is not None:
            entities.append(meter("gas", "ONEp1 Gas", lambda m: _get(m, "energy", "gas"),
                                  {"device_class": SensorDeviceClass.GAS, "state_class": SensorStateClass.TOTAL_INCREASING, "unit": UnitOfVolume.CUBIC_METERS}, True))
        if energy.get("water") is not None:
            entities.append(meter("water", "ONEp1 Water", lambda m: _get(m, "energy", "water"),
                                  {"device_class": SensorDeviceClass.WATER, "state_class": SensorStateClass.TOTAL_INCREASING, "unit": UnitOfVolume.CUBIC_METERS}, True))

        for p_idx, phase in enumerate(_get(m, "power", "phases") or []):
            if phase is None:
                continue
            n = p_idx + 1
            entities += [
                meter(f"power_l{n}", f"Vermogen L{n}", lambda m, i=p_idx: _get(m, "power", "phases", i, "net_kw"), _power()),
                meter(f"voltage_l{n}", f"Spanning L{n}", lambda m, i=p_idx: _get(m, "power", "phases", i, "voltage_v"),
                      _power(SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT), category=EntityCategory.DIAGNOSTIC),
                meter(f"current_l{n}", f"Stroom L{n}", lambda m, i=p_idx: _get(m, "power", "phases", i, "current_a"),
                      _power(SensorDeviceClass.CURRENT, UnitOfElectricCurrent.AMPERE)),
            ]

        for ch in range(len(m.get("channels") or [])):
            entities.append(ONEp1ChannelSensor(coordinator, entry, code, ch, legacy(f"ch{ch}")))

        # Energieprijs hoort bij het account; hij komt bij de eerste ONEp1.
        if first and data.get("price") is not None:
            entities += [
                ONEp1PriceSensor(coordinator, entry, code, "price_buy", "Stroomprijs", "buy"),
                ONEp1PriceSensor(coordinator, entry, code, "price_sell", "Terugleverprijs", "sell"),
                ONEp1PriceSensor(coordinator, entry, code, "price_spot", "Beursprijs", "spot"),
            ]

    for s in data.get("solarone") or []:
        code = s["pairing_code"]
        entities += [
            ONEp1SolarSensor(coordinator, entry, code, "power", "Vermogen", lambda d: _get(d, "ac_power_w"), _power(unit=UnitOfPower.WATT)),
            ONEp1SolarSensor(coordinator, entry, code, "today", "Opbrengst vandaag", lambda d: _get(d, "today_kwh"), _energy()),
            ONEp1SolarSensor(coordinator, entry, code, "total", "Totale opbrengst", lambda d: _get(d, "total_kwh"), _energy()),
            ONEp1SolarSensor(coordinator, entry, code, "applied_limit", "Toegepaste limiet", lambda d: _get(d, "applied_limit_percent"),
                             {"device_class": None, "state_class": SensorStateClass.MEASUREMENT, "unit": PERCENTAGE}, icon="mdi:solar-power-variant"),
            ONEp1SolarSensor(coordinator, entry, code, "reason", "Status besturing", lambda d: _reason(_get(d, "applied_reason")), None,
                             icon="mdi:information-outline", category=EntityCategory.DIAGNOSTIC),
        ]
        for i, inv in enumerate(s.get("inverters") or []):
            name = inv.get("name") or inv.get("id")
            entities += [
                ONEp1SolarSensor(coordinator, entry, code, f"{inv['id']}_power", f"{name} vermogen",
                                 lambda d, i=i: _get(d, "inverters", i, "ac_power_w"), _power(unit=UnitOfPower.WATT)),
                ONEp1SolarSensor(coordinator, entry, code, f"{inv['id']}_today", f"{name} opbrengst vandaag",
                                 lambda d, i=i: _get(d, "inverters", i, "today_kwh"), _energy()),
            ]

    for b in data.get("batteryone") or []:
        code = b["pairing_code"]
        soc = {"device_class": SensorDeviceClass.BATTERY, "state_class": SensorStateClass.MEASUREMENT, "unit": PERCENTAGE}
        entities += [
            ONEp1BatterySensor(coordinator, entry, code, "soc", "Laadniveau", lambda d: _get(d, "soc_pct"), soc),
            ONEp1BatterySensor(coordinator, entry, code, "power", "Vermogen", lambda d: _get(d, "power_w"), _power(unit=UnitOfPower.WATT),
                               attrs=lambda d: {"teken": "positief = ontladen, negatief = laden"}),
            ONEp1BatterySensor(coordinator, entry, code, "setpoint", "Gevraagd vermogen", lambda d: _get(d, "applied_total_w"),
                               _power(unit=UnitOfPower.WATT), category=EntityCategory.DIAGNOSTIC),
            ONEp1BatterySensor(coordinator, entry, code, "reason", "Status besturing", lambda d: _reason(_get(d, "applied_reason")), None,
                               icon="mdi:information-outline", category=EntityCategory.DIAGNOSTIC),
        ]
        for i, bat in enumerate(b.get("batteries") or []):
            name = bat.get("name") or bat.get("id")
            entities += [
                ONEp1BatterySensor(coordinator, entry, code, f"{bat['id']}_soc", f"{name} laadniveau",
                                   lambda d, i=i: _get(d, "batteries", i, "soc_pct"), soc),
                ONEp1BatterySensor(coordinator, entry, code, f"{bat['id']}_power", f"{name} vermogen",
                                   lambda d, i=i: _get(d, "batteries", i, "power_w"), _power(unit=UnitOfPower.WATT)),
            ]

    async_add_entities(entities)


def _reason(code):
    if not code:
        return None
    return REASONS.get(code, code)


class _ValueMixin:
    """Gedeelde opzet: naam, eenheid, klasse en een functie die de waarde uit de apparaatdata haalt."""

    def _setup(self, name, value, spec, icon=None, category=None, attrs=None):
        self._attr_name = name
        self._value = value
        self._attrs = attrs
        if spec:
            self._attr_device_class = spec.get("device_class")
            self._attr_state_class = spec.get("state_class")
            self._attr_native_unit_of_measurement = spec.get("unit")
        if icon:
            self._attr_icon = icon
        if category:
            self._attr_entity_category = category

    def _source(self):
        raise NotImplementedError

    @property
    def native_value(self):
        src = self._source()
        return self._value(src) if src is not None else None

    @property
    def extra_state_attributes(self):
        src = self._source()
        return self._attrs(src) if self._attrs and src is not None else None


class ONEp1MeterSensor(_ValueMixin, ONEp1MeterEntity, SensorEntity):
    def __init__(self, coordinator, entry, code, key, name, value, spec, legacy_uid=None, category=None, attrs=None):
        super().__init__(coordinator, entry, code, key, legacy_uid)
        self._setup(name, value, spec, category=category, attrs=attrs)

    def _source(self):
        return self.meter


class ONEp1SolarSensor(_ValueMixin, ONEp1SolarEntity, SensorEntity):
    def __init__(self, coordinator, entry, code, key, name, value, spec, icon=None, category=None):
        super().__init__(coordinator, entry, code, key)
        self._setup(name, value, spec, icon, category)

    def _source(self):
        return self.dev


class ONEp1BatterySensor(_ValueMixin, ONEp1BatteryEntity, SensorEntity):
    def __init__(self, coordinator, entry, code, key, name, value, spec, icon=None, category=None, attrs=None):
        super().__init__(coordinator, entry, code, key)
        self._setup(name, value, spec, icon, category, attrs)

    def _source(self):
        return self.dev


class ONEp1PriceSensor(ONEp1MeterEntity, SensorEntity):
    """Energieprijs van nu op het eigen contract (afname, teruglevering) en de kale beursprijs."""

    _attr_native_unit_of_measurement = PRICE_UNIT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:currency-eur"
    _attr_suggested_display_precision = 3

    def __init__(self, coordinator, entry, code, key, name, field):
        super().__init__(coordinator, entry, code, key)
        self._attr_name = name
        self._field = field

    @property
    def available(self):
        return super().available and (self.coordinator.data or {}).get("price") is not None

    @property
    def native_value(self):
        return _get(self.coordinator.data, "price", self._field)

    @property
    def extra_state_attributes(self):
        price = (self.coordinator.data or {}).get("price") or {}
        def hours(lst):
            return [{"hour": p.get("hour"), "price": p.get(self._field)} for p in lst or []]
        return {
            "contract": price.get("label"),
            "dynamic": price.get("dynamic"),
            "today": hours(price.get("today")),
            "tomorrow": hours(price.get("tomorrow")) if price.get("tomorrow") else None,
        }


class ONEp1ChannelSensor(ONEp1MeterEntity, SensorEntity):
    """Status van een uitgang (ongewijzigd t.o.v. 1.x, zelfde unique_id voor de eerste ONEp1)."""

    _attr_icon = "mdi:flash"

    def __init__(self, coordinator, entry, code, channel_index, legacy_uid):
        super().__init__(coordinator, entry, code, f"ch{channel_index}", legacy_uid)
        self._channel_index = channel_index
        self._attr_name = f"ONEp1 Kanaal {channel_index}"

    def _channel(self):
        return _get(self.meter, "channels", self._channel_index)

    @property
    def native_value(self):
        channel = self._channel()
        if not channel:
            return None
        if not channel.get("active", False):
            return "uit"
        return f"prio {channel.get('priority', '?')} | max {channel.get('maxPower', '?')} kW"

    @property
    def extra_state_attributes(self):
        channel = self._channel()
        if not channel:
            return {}
        return {
            "name": channel.get("name"),
            "active": channel.get("active"),
            "priority": channel.get("priority"),
            "max_power_kw": channel.get("maxPower"),
            "reaction_time_s": channel.get("reactionTime"),
            "threshold_power_kw": channel.get("thresholdPower"),
            "is_battery": channel.get("isBattery"),
            "is_meter": channel.get("isMeter"),
            "economic_mode": channel.get("economicMode"),
        }
