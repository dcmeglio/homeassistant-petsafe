"""Config flow for PetSafe Integration."""
from __future__ import annotations

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from botocore.exceptions import ParamValidationError
from homeassistant import config_entries
from homeassistant.const import (CONF_ACCESS_TOKEN, CONF_BASE, CONF_CODE,
                                 CONF_EMAIL, CONF_TOKEN)
from homeassistant.data_entry_flow import FlowResult

import petsafe

from .const import CONF_REFRESH_TOKEN, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_EMAIL): str})
STEP_CODE_DATA_SCHEMA = vol.Schema({vol.Required(CONF_CODE): str})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PetSafe Integration."""

    def __init__(self):

        self.data: dict = {}
        self._client = None
        self._id_token = None
        self._access_token = None
        self._refresh_token = None

        self._feeders = None
        self._litterboxes = None

    VERSION = 1

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )
        else:
            try:
                await self.get_email_code(user_input[CONF_EMAIL])
                self.data = user_input
                return await self.async_step_code()
            except petsafe.client.InvalidUserException:
                errors[CONF_EMAIL] = "invalid_user"
            except Exception:
                errors[CONF_BASE] = "cannot_connect"

            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )

    async def async_step_code(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is None:
            return self.async_show_form(
                step_id="code", data_schema=STEP_CODE_DATA_SCHEMA
            )
        else:
            try:
                await self.get_devices(self.data[CONF_EMAIL], user_input[CONF_CODE])
                return await self.async_step_devices()
            except ParamValidationError:
                errors[CONF_CODE] = "invalid_code"
            except petsafe.client.InvalidCodeException:
                errors[CONF_CODE] = "invalid_code"
            except Exception:
                errors[CONF_BASE] = "unknown_error"
            return self.async_show_form(
                step_id="code", data_schema=STEP_CODE_DATA_SCHEMA, errors=errors
            )

    async def async_step_devices(self, user_input: dict[str, Any] | None = None):
        if user_input is None:
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
        else:
            self.data.update(user_input)
            self.data[CONF_TOKEN] = self._id_token
            self.data[CONF_ACCESS_TOKEN] = self._access_token
            self.data[CONF_REFRESH_TOKEN] = self._refresh_token
            return self.async_create_entry(title=self.data[CONF_EMAIL], data=self.data)

    async def get_email_code(self, email):
        self._client = petsafe.PetSafeClient(email=email)
        await self._client.request_code()
        return True

    async def get_devices(self, email, code):
        await self._client.request_tokens_from_code(code)
        self._id_token = self._client.id_token
        self._access_token = self._client.access_token
        self._refresh_token = self._client.refresh_token

        self._feeders = {
            x.api_name: x.friendly_name for x in await self._client.get_feeders()
        }
        self._litterboxes = {
            x.api_name: x.friendly_name for x in await self._client.get_litterboxes()
        }
        return True
