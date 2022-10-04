"""The PetSafe Integration integration."""
from __future__ import annotations

import async_timeout
import boto3
from .helpers import get_feeders_for_service

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_AREA_ID, ATTR_DEVICE_ID, ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_EMAIL, CONF_TOKEN
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_REFRESH_TOKEN,
    DOMAIN,
    SERVICE_ADD_SCHEDULE,
    SERVICE_DELETE_ALL_SCHEDULES,
    SERVICE_DELETE_SCHEDULE,
    SERVICE_MODIFY_SCHEDULE,
    ATTR_TIME,
    ATTR_AMOUNT,
)

import petsafe

from datetime import timedelta

import logging

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.SELECT,
]


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

    hass.data[DOMAIN][entry.entry_id] = coordinator

    def handle_add_schedule(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        time = call.data.get(ATTR_TIME)
        amount = call.data.get(ATTR_AMOUNT)
        matched_devices = get_feeders_for_service(
            hass, area_ids, device_ids, entity_ids
        )
        for device_id in matched_devices:
            # Kind of a hack but it will work for now
            data = {}
            data["thing_name"] = device_id
            device = petsafe.devices.DeviceSmartFeed(client, data)
            device.schedule_feed(time, amount, False)

    hass.services.async_register(DOMAIN, SERVICE_ADD_SCHEDULE, handle_add_schedule)

    # hass.services.async_register(
    #     DOMAIN, SERVICE_DELETE_SCHEDULE, handle_delete_schedule
    # )
    # hass.services.async_register(
    #     DOMAIN, SERVICE_DELETE_ALL_SCHEDULES, handle_delete_all_schedules
    # )
    # hass.services.async_register(
    #     DOMAIN, SERVICE_MODIFY_SCHEDULE, handle_modify_schedule
    # )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await coordinator.async_config_entry_first_refresh()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def handle_delete_schedule(call):
    pass


def handle_delete_all_schedules(call):
    pass


def handle_modify_schedule(call):
    pass


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
        """Fetch data from API endpoint."""
        cognito_idp = await self.hass.async_add_executor_job(
            boto3.client, "cognito-idp", "us-east-1"
        )

        try:
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
        except cognito_idp.exceptions.NotAuthorizedException:
            raise ConfigEntryAuthFailed()
