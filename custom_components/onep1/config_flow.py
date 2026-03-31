"""Config flow for ONEp1 integration."""

import logging

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, API_BASE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_api_key(hass: HomeAssistant, api_key: str) -> dict:
    """Validate the API key by making a test request."""
    async with aiohttp.ClientSession() as session:
        headers = {"x-api-key": api_key}
        async with session.get(
            f"{API_BASE_URL}/power",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            if response.status == 401:
                raise InvalidAuth
            if response.status == 403:
                raise NoSubscription
            if response.status != 200:
                raise CannotConnect
            data = await response.json()
            return data


class ONEp1ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ONEp1."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                await validate_api_key(self.hass, user_input[CONF_API_KEY])
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except NoSubscription:
                errors["base"] = "no_subscription"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_API_KEY][:16])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="ONEp1 Energie Manager",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )


class InvalidAuth(Exception):
    """Error to indicate invalid authentication."""


class NoSubscription(Exception):
    """Error to indicate no active subscription."""


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""
