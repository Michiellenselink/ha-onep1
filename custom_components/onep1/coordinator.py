"""Data update coordinator for ONEp1."""

import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE_URL, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class ONEp1Coordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from ONEp1 API."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="ONEp1",
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.api_key = api_key
        self._session = None

    async def _async_update_data(self):
        """Fetch data from ONEp1 API."""
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()

            headers = {"x-api-key": self.api_key}

            # Fetch status data
            async with self._session.get(
                f"{API_BASE_URL}/status", headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 401:
                    raise UpdateFailed("Ongeldige API key")
                if response.status == 403:
                    raise UpdateFailed("Abonnement vereist")
                if response.status != 200:
                    raise UpdateFailed(f"API error: {response.status}")
                data = await response.json()

            # Fetch energy meter readings (kWh totals for HA Energy dashboard)
            try:
                async with self._session.get(
                    f"{API_BASE_URL}/energy", headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as energy_response:
                    if energy_response.status == 200:
                        data["energy"] = await energy_response.json()
            except Exception:
                pass  # Energy data is optional

            return data

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Verbindingsfout: {err}") from err

    async def async_set_channel(self, channel_index: int, settings: dict):
        """Update a channel's settings."""
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()

            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
            }

            async with self._session.put(
                f"{API_BASE_URL}/channel/{channel_index}",
                headers=headers,
                json=settings,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error("Failed to update channel %d: %s", channel_index, text)
                    return False
                return True

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error updating channel: %s", err)
            return False

    async def async_shutdown(self):
        """Close the session."""
        if self._session:
            await self._session.close()
            self._session = None
