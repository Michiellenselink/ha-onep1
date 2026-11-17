"""Data update coordinator for ONEp1."""

import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE_URL, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)
TIMEOUT = aiohttp.ClientTimeout(total=15)


class ONEp1Coordinator(DataUpdateCoordinator):
    """Haalt elke 10 s alles op in één aanroep (GET /api/ha/v2/state)."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="ONEp1",
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.api_key = api_key
        self._session = async_get_clientsession(hass)

    @property
    def _headers(self):
        return {"x-api-key": self.api_key}

    async def _async_update_data(self):
        try:
            async with self._session.get(
                f"{API_BASE_URL}/v2/state", headers=self._headers, timeout=TIMEOUT
            ) as response:
                if response.status == 401:
                    raise UpdateFailed("Ongeldige API key")
                if response.status == 403:
                    raise UpdateFailed("Actief ONEp1-abonnement vereist")
                if response.status != 200:
                    raise UpdateFailed(f"API error: {response.status}")
                return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Verbindingsfout: {err}") from err

    # ------------------------------------------------------------------
    # Opzoeken in de laatste data
    # ------------------------------------------------------------------
    def _find(self, key, code):
        for item in (self.data or {}).get(key) or []:
            if item.get("pairing_code") == code:
                return item
        return None

    def meter(self, code):
        return self._find("meters", code)

    def solarone(self, code):
        return self._find("solarone", code)

    def batteryone(self, code):
        return self._find("batteryone", code)

    def first_meter_code(self):
        meters = (self.data or {}).get("meters") or []
        return meters[0]["pairing_code"] if meters else None

    def signature(self):
        """Welke entiteiten er moeten bestaan, als verzameling kenmerken.

        Kenmerken met een ':' erin (fase, gas, water, omvormer, accu) hangen af van meetdata die
        even kan wegvallen; alleen de dongels zelf staan er zonder ':' in.
        """
        data = self.data or {}
        feats = set()
        for m in data.get("meters") or []:
            code = m.get("pairing_code")
            feats.add(f"meter {code}")
            for i, p in enumerate((m.get("power") or {}).get("phases") or []):
                if p is not None:
                    feats.add(f"meter {code}:phase{i + 1}")
            energy = m.get("energy") or {}
            for k in ("gas", "water"):
                if energy.get(k) is not None:
                    feats.add(f"meter {code}:{k}")
            feats.add(f"meter {code}:channels{len(m.get('channels') or [])}")
        for s in data.get("solarone") or []:
            feats.add(f"solarone {s.get('pairing_code')}")
            feats.update(f"solarone {s.get('pairing_code')}:{i.get('id')}" for i in s.get("inverters") or [])
        for b in data.get("batteryone") or []:
            feats.add(f"batteryone {b.get('pairing_code')}")
            feats.update(f"batteryone {b.get('pairing_code')}:{x.get('id')}" for x in b.get("batteries") or [])
        if data.get("price") is not None:
            feats.add("price:on")
        return frozenset(feats)

    @staticmethod
    def needs_reload(old, new):
        """Herladen als er iets bijkomt, of als een dongel verdwijnt (ontkoppeld).

        Valt alleen meetdata weg (fase, gas, prijs …), dan niet: dat is meestal tijdelijk en de
        entiteit blijft gewoon bestaan (zonder waarde).
        """
        if new - old:
            return True
        return any(":" not in f for f in old - new)

    # ------------------------------------------------------------------
    # Schrijven
    # ------------------------------------------------------------------
    async def _put(self, path, body):
        try:
            async with self._session.put(
                f"{API_BASE_URL}{path}",
                headers={**self._headers, "Content-Type": "application/json"},
                json=body,
                timeout=TIMEOUT,
            ) as response:
                try:
                    data = await response.json()
                except (aiohttp.ContentTypeError, ValueError):
                    data = {}
                if response.status == 403 and data.get("code") == "ha_control_disabled":
                    raise ServiceValidationError(
                        "Besturing door Home Assistant staat uit. Zet hem aan in het ONEp1 dashboard "
                        "(Instellingen > Home Assistant)."
                    )
                if response.status in (400, 403, 404):
                    raise ServiceValidationError(data.get("error") or f"ONEp1 weigerde dit ({response.status})")
                if response.status != 200:
                    raise HomeAssistantError(data.get("error") or f"ONEp1 gaf fout {response.status}")
                return data
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise HomeAssistantError(f"Verbindingsfout met ONEp1: {err}") from err

    def _replace(self, key, item):
        if not self.data or not item:
            return
        lst = self.data.get(key) or []
        for i, old in enumerate(lst):
            if old.get("pairing_code") == item.get("pairing_code"):
                lst[i] = item
        self.async_update_listeners()

    async def async_set_channel(self, code, channel_index: int, settings: dict):
        """Uitgang van een ONEp1 aanpassen (code = koppelcode van de meter)."""
        data = await self._put(f"/v2/meter/{code}/channel/{channel_index}", settings)
        meter = self.meter(code)
        if meter and data.get("channel"):
            chans = meter.get("channels") or []
            if 0 <= channel_index < len(chans):
                chans[channel_index] = data["channel"]
            self.async_update_listeners()
        await self.async_request_refresh()

    async def async_set_solarone(self, code, settings: dict):
        data = await self._put(f"/v2/solarone/{code}", settings)
        self._replace("solarone", data.get("solarone"))
        await self.async_request_refresh()

    async def async_set_batteryone(self, code, settings: dict):
        data = await self._put(f"/v2/batteryone/{code}", settings)
        self._replace("batteryone", data.get("batteryone"))
        await self.async_request_refresh()
