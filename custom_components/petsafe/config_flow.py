"""Config flow for PetSafe Integration integration."""
from __future__ import annotations

import logging
from os import access
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import CONF_CODE, CONF_EMAIL
import homeassistant.helpers.config_validation as cv

import petsafe

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_EMAIL): str})
STEP_CODE_DATA_SCHEMA = vol.Schema({vol.Required(CONF_CODE): str})


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self) -> None:
        """Initialize."""

    async def authenticate(self, username: str, password: str) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = PlaceholderHub()

    if not await hub.authenticate(data["username"], data["password"]):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Name of the device"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PetSafe Integration."""

    def __init__(self):
        self._token = ""
        self.data: dict = {}
        self._client = None

        self._feeders = None
        self._litterboxes = None

    VERSION = 1

    def get_email_code(self, email):
        self._client = petsafe.PetSafeClient(email=email)
        self._client.request_code()
        return True

    def get_devices(self, email, code):
        self._client.request_tokens_from_code(code)

        self._feeders = {
            x.api_name: x.friendly_name
            for x in petsafe.devices.get_feeders(self._client)
        }
        self._litterboxes = {
            x.api_name: x.friendly_name
            for x in petsafe.devices.get_litterboxes(self._client)
        }
        return True

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )
        else:
            await self.hass.async_add_executor_job(
                self.get_email_code, user_input[CONF_EMAIL]
            )
            self.data = user_input
            return await self.async_step_code()

    async def async_step_code(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="code", data_schema=STEP_CODE_DATA_SCHEMA
            )
        else:
            await self.hass.async_add_executor_job(
                self.get_devices, self.data[CONF_EMAIL], user_input[CONF_CODE]
            )
            return await self.async_step_devices()

    async def async_step_devices(self, user_input: dict[str, Any] | None = None):
        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "feeders", default=list(self._feeders)
                    ): cv.multi_select(self._feeders),
                    vol.Required(
                        "litterboxes", default=list(self._litterboxes)
                    ): cv.multi_select(self._litterboxes),
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
