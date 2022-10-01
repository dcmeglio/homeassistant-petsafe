"""The PetSafe Integration integration."""
from __future__ import annotations

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_CODE, CONF_EMAIL, CONF_TOKEN

from .const import CONF_REFRESH_TOKEN, DOMAIN

import petsafe

from datetime import timedelta

import logging

import asyncio

_LOGGER = logging.getLogger(__name__)

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


def get_api(email, id_token, refresh_token, access_token):
    return petsafe.PetSafeClient(email, id_token, refresh_token, access_token)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PetSafe Integration from a config entry."""
    client = await hass.async_add_executor_job(
        get_api,
        entry.data.get(CONF_EMAIL),
        entry.data.get(CONF_TOKEN),
        entry.data.get(CONF_REFRESH_TOKEN),
        entry.data.get(CONF_ACCESS_TOKEN),
    )
    hass.data.setdefault(DOMAIN, {})

    coordinator = PetSafeCoordinator(hass, client)

    hass.data[DOMAIN] = coordinator

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await coordinator.async_config_entry_first_refresh()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class PetSafeData:
    def __init__(self, feeders, litterboxes):
        self.feeders = feeders
        self.litterboxes = litterboxes


class PetSafeCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, api):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="PetSafe",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self.api = api
        self.hass: HomeAssistant = hass

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        #     try:
        # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        # handled by the data update coordinator.
        async with async_timeout.timeout(10):
            feeders = await self.hass.async_add_executor_job(
                petsafe.devices.get_feeders, self.api
            )
            scoopers = await self.hass.async_add_executor_job(
                petsafe.devices.get_litterboxes, self.api
            )
            return PetSafeData(feeders, scoopers)

    #  except ApiAuthError as err:
    # Raising ConfigEntryAuthFailed will cancel future updates
    # and start a config flow with SOURCE_REAUTH (async_step_reauth)
    #    raise ConfigEntryAuthFailed from err
    # except ApiError as err:
    #     raise UpdateFailed(f"Error communicating with API: {err}")
