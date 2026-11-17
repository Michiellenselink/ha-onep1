# ONEp1 - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Michiellenselink/ha-onep1)](https://github.com/Michiellenselink/ha-onep1/releases)

Home Assistant-integratie (via HACS) voor de [ONEp1 Energie Manager](https://onep1.nl): slimme P1-meter dongle met 4 uitgangen voor het aansturen van apparaten op zonne-overschot en dynamische energieprijzen. Ook voor de **solarONE** (omvormerbesturing) en **batteryONE** (thuisaccubesturing).

## Features

- **Real-time energiedata**: verbruik, teruglevering en netto vermogen (kW, elke 10 seconden), ook per fase met spanning en stroom
- **Meterstanden**: verbruik en teruglevering (kWh, totaal en per tarief) + gas en water (m³) voor het HA Energie dashboard
- **Energieprijs**: wat je nu betaalt en terugkrijgt op je eigen contract, plus de beursprijs en de uurprijzen van vandaag en morgen
- **Uitgangen bedienen**: per uitgang een schakelaar (aan/uit, economisch verbruik), max vermogen en prioriteit
- **solarONE**: opwek per omvormer; besturing, modus en vermogenslimiet instellen
- **batteryONE**: laadniveau en vermogen per accu; besturing, modus en handmatig vermogen instellen
- **Elke dongel een eigen apparaat**; een nieuw gekoppelde dongel verschijnt vanzelf
- **UI configuratie**: instellen via Instellingen > Integraties (geen YAML nodig)

## Installatie

### Via HACS (aanbevolen)

ONEp1 staat in de standaardlijst van HACS. Je hoeft de repository dus niet zelf toe te voegen.

1. Open **HACS** in Home Assistant
2. Zoek **"ONEp1"** en klik **Download**
3. **Herstart** Home Assistant

> Vind je ONEp1 niet (oudere HACS-versie)? Voeg dan via **HACS** → menu (⋮) → **Custom repositories** de repository `https://github.com/Michiellenselink/ha-onep1` toe, categorie **Integration**.

### Handmatig

1. Download de [laatste release](https://github.com/Michiellenselink/ha-onep1/releases) of via het [ONEp1 dashboard](https://onep1.nl/dashboard.html)
2. Kopieer de `custom_components/onep1/` map naar je HA `config/custom_components/`
3. **Herstart** Home Assistant

### Configuratie

1. Ga naar **Instellingen** → **Apparaten en diensten** → **Integratie toevoegen**
2. Zoek **"ONEp1"**
3. Voer je **API Key** in (genereer deze in het [ONEp1 dashboard](https://onep1.nl/dashboard.html) onder Instellingen > Home Assistant)

## Entiteiten

### ONEp1 (slimme meter)

| Entiteit | Eenheid | Beschrijving |
|----------|---------|--------------|
| ONEp1 Verbruik / Teruglevering | kW | Huidig vermogen van/naar het net |
| Netto vermogen | kW | Verbruik min teruglevering |
| ONEp1 Verbruik Totaal / Teruglevering Totaal | kWh | Meterstanden (voor het Energie dashboard) |
| Verbruik / Teruglevering T1 (dal), T2 (normaal) | kWh | Meterstanden per tarief |
| ONEp1 Gas | m³ | Gasmeterstand |
| ONEp1 Water | m³ | Watermeterstand (alleen met een slimme watermeter op de P1-poort) |
| Vermogen / Stroom / Spanning L1-L3 | kW / A / V | Per fase (eenfase: alleen L1). Stroom is berekend uit vermogen en spanning |
| Stroomprijs / Terugleverprijs / Beursprijs | EUR/kWh | Prijs van dit uur op je eigen contract; uurlijst van vandaag en morgen als attribuut |
| Kanaal 0-3 aan, economisch verbruik | schakelaar | Uitgang aan/uit en economisch verbruik |
| Kanaal 0-3 max vermogen | kW | Planningshint voor het verdeelalgoritme |
| Kanaal 0-3 prioriteit | 1-4 | Volgorde van de uitgangen |
| ONEp1 Kanaal 0-3 | - | Status per uitgang met attributen (zoals in 1.x) |
| Online, Besturing door Home Assistant | aan/uit | Diagnose |

### solarONE (omvormerbesturing)

| Entiteit | Eenheid | Beschrijving |
|----------|---------|--------------|
| Vermogen, Opbrengst vandaag, Totale opbrengst | W / kWh | Alle omvormers samen, en per omvormer |
| Besturing | schakelaar | Besturing aan/uit |
| Modus | keuze | Handmatig, Nul op de meter, Energieprijs, Beperken bij negatieve prijs |
| Vermogenslimiet | % | Limiet in de modus Handmatig |
| Toegepaste limiet, Status besturing | % / tekst | Wat de solarONE nu doet en waarom |

### batteryONE (thuisaccubesturing)

| Entiteit | Eenheid | Beschrijving |
|----------|---------|--------------|
| Laadniveau, Vermogen | % / W | Alle accu's samen, en per accu. Vermogen positief = ontladen, negatief = laden |
| Besturing | schakelaar | Besturing aan/uit |
| Modus | keuze | Handmatig, Nul op de meter, Energieprijs, Slim (voorspellend) |
| Handmatig vermogen | W | Vermogen in de modus Handmatig (negatief = laden) |
| Gevraagd vermogen, Status besturing | W / tekst | Wat de batteryONE nu vraagt en waarom |

## Besturing door Home Assistant

In het ONEp1 dashboard (Instellingen > Home Assistant) staat een schakelaar **"Besturing door Home Assistant"**:

- **Aan**: HA mag de uitgangen aanpassen (het dashboard kan dat dan niet meer) en de besturing, modus en limiet van je solarONE en batteryONE
- **Uit**: HA kijkt alleen mee; de schakelaars en keuzelijsten geven een melding dat de besturing uit staat

## Service: onep1.set_channel

Pas uitgangen aan via automatiseringen (de schakelaars en keuzelijsten hierboven doen hetzelfde):

```yaml
service: onep1.set_channel
data:
  channel: 0          # Kanaalnummer (0-3)
  meter: "12345"      # Optioneel: koppelcode van de ONEp1 (leeg = je eerste ONEp1)
  active: true        # Kanaal aan/uit
  priority: 1         # Prioriteit (1-4)
  maxPower: 3.6       # Max vermogen (kW)
  reactionTime: 10    # Reactietijd (seconden)
  thresholdPower: 0.5 # Surplus drempel (kW)
  isBattery: false    # Thuisaccu modus
  isMeter: false      # Meter modus (passthrough)
  economicMode: true  # Economisch verbruik (dynamische prijzen)
```

## Voorbeeld automatiseringen

```yaml
automation:
  - alias: "EV lader uit als niet thuis"
    trigger:
      - platform: state
        entity_id: person.jouw_naam
        to: "not_home"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.onep1_energie_manager_kanaal_0_aan

  - alias: "Accu laden onder 10 cent"
    trigger:
      - platform: numeric_state
        entity_id: sensor.onep1_energie_manager_stroomprijs
        below: 0.10
    action:
      - service: select.select_option
        target:
          entity_id: select.batteryone_garage_modus
        data:
          option: "Handmatig"
      - service: number.set_value
        target:
          entity_id: number.batteryone_garage_handmatig_vermogen
        data:
          value: -2000   # negatief = laden
```

De entity-namen van solarONE en batteryONE hangen af van de naam in het ONEp1 dashboard (hier "Garage").

## HA Energie Dashboard

- **Van netwerk geïmporteerde energie** → ONEp1 Verbruik Totaal (of per tarief T1/T2)
- **Naar netwerk geëxporteerde energie** → ONEp1 Teruglevering Totaal (of per tarief T1/T2)
- **Prijs** → Stroomprijs en Terugleverprijs (kies "entiteit met huidige prijs")
- **Gas** → ONEp1 Gas
- **Water** → ONEp1 Water
- **Zonnepanelen** → solarONE Opbrengst vandaag of Totale opbrengst

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
