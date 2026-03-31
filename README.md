# ONEp1 - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Michiellenselink/ha-onep1)](https://github.com/Michiellenselink/ha-onep1/releases)

Home Assistant custom integration voor de [ONEp1 Energie Manager](https://onep1.nl) - slimme P1 meter dongle met 4-poorts multiplexer voor het aansturen van apparaten op zonne-energie overschot en dynamische energieprijzen.

## Features

- **Real-time energiedata** — verbruik en teruglevering (kW, elke 10 seconden)
- **Meterstanden** — totaal verbruik en teruglevering (kWh) + gas (m³) voor het HA Energie dashboard
- **4 kanaal sensoren** — status per uitgang met attributen (prioriteit, max vermogen, reactietijd, etc.)
- **Kanaal bediening** — via `onep1.set_channel` service in automatiseringen
- **HA Energie dashboard** — compatible sensoren voor import, export en gas
- **UI configuratie** — instellen via Instellingen > Integraties (geen YAML nodig)

## Installatie

### Via HACS (aanbevolen)

1. Open **HACS** in Home Assistant
2. Ga naar **Integraties** → menu (⋮) → **Custom repositories**
3. Voeg toe: `https://github.com/Michiellenselink/ha-onep1` | Categorie: **Integration**
4. Zoek **"ONEp1"** en klik **Download**
5. **Herstart** Home Assistant

### Handmatig

1. Download de [laatste release](https://github.com/Michiellenselink/ha-onep1/releases) of via het [ONEp1 dashboard](https://onep1.nl/dashboard.html)
2. Kopieer de `custom_components/onep1/` map naar je HA `config/custom_components/`
3. **Herstart** Home Assistant

### Configuratie

1. Ga naar **Instellingen** → **Apparaten en diensten** → **Integratie toevoegen**
2. Zoek **"ONEp1"**
3. Voer je **API Key** in (genereer deze in het [ONEp1 dashboard](https://onep1.nl/dashboard.html) onder Instellingen > Home Assistant)

## Sensoren

Na installatie verschijnen automatisch:

| Sensor | Type | Eenheid | Beschrijving |
|--------|------|---------|-------------|
| ONEp1 Verbruik | power | kW | Huidig verbruik van het net |
| ONEp1 Teruglevering | power | kW | Huidige teruglevering aan het net |
| ONEp1 Verbruik Totaal | energy | kWh | Meterstand verbruik (voor Energie dashboard) |
| ONEp1 Teruglevering Totaal | energy | kWh | Meterstand teruglevering (voor Energie dashboard) |
| ONEp1 Gas | gas | m³ | Gasmeterstand (voor Energie dashboard) |
| ONEp1 Kanaal 0-3 | - | - | Status per kanaal met attributen |

## Service: onep1.set_channel

Pas kanaalinstellingen aan via automatiseringen:

```yaml
service: onep1.set_channel
data:
  channel: 0          # Kanaalnummer (0-3)
  active: true        # Kanaal aan/uit
  priority: 1         # Prioriteit (1-4)
  maxPower: 3.6       # Max vermogen (kW)
  reactionTime: 10    # Reactietijd (seconden)
  thresholdPower: 0.5 # Surplus drempel (kW)
  isBattery: false    # Thuisaccu modus
  isMeter: false      # Meter modus (passthrough)
  economicMode: true  # Economic mode (dynamische prijzen)
```

## Voorbeeld automatisering

```yaml
automation:
  - alias: "EV lader uit als niet thuis"
    trigger:
      - platform: state
        entity_id: person.jouw_naam
        to: "not_home"
    action:
      - service: onep1.set_channel
        data:
          channel: 0
          active: false

  - alias: "Warmtepomp prioriteit 1 bij vorst"
    trigger:
      - platform: numeric_state
        entity_id: weather.thuis
        attribute: temperature
        below: 5
    action:
      - service: onep1.set_channel
        data:
          channel: 0
          priority: 1
          maxPower: 5.0
```

## HA Energie Dashboard

Configureer het Energie dashboard met:

- **Van netwerk geïmporteerde energie** → ONEp1 Verbruik Totaal
- **Naar netwerk geëxporteerde energie** → ONEp1 Teruglevering Totaal
- **Gas** → ONEp1 Gas

## Besturing toggle

In het ONEp1 dashboard (Instellingen > Home Assistant) staat een schakelaar **"Besturing door Home Assistant"**:

- **Aan** — alleen HA kan kanaalinstellingen wijzigen
- **Uit** — alleen het dashboard kan wijzigen

Dit voorkomt dat beide bronnen elkaars instellingen overschrijven.

## Vereisten

- ONEp1 dongle met actief abonnement
- Home Assistant 2024.1.0 of nieuwer
- API Key (genereer via het ONEp1 dashboard)

## Links

- [ONEp1 Website](https://onep1.nl)
- [Kennisbank artikel](https://onep1.nl/kennisbank/home-assistant-integratie.html)
- [Issues](https://github.com/Michiellenselink/ha-onep1/issues)

## Licentie

MIT License - Zie [LICENSE](LICENSE)
