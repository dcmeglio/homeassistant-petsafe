"""The PetSafe Integration integration."""
from __future__ import annotations
import asyncio

import async_timeout
import boto3
import httpx
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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PetSafe Integration from a config entry."""
    client = petsafe.PetSafeClient(
        entry.data.get(CONF_EMAIL),
        entry.data.get(CONF_TOKEN),
        entry.data.get(CONF_REFRESH_TOKEN),
        entry.data.get(CONF_ACCESS_TOKEN),
    )

    hass.data.setdefault(DOMAIN, {})

    coordinator = PetSafeCoordinator(hass, client)

    hass.data[DOMAIN][entry.entry_id] = coordinator

    async def handle_add_schedule(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        time = call.data.get(ATTR_TIME)
        amount = call.data.get(ATTR_AMOUNT)
        matched_devices = get_feeders_for_service(
            hass, area_ids, device_ids, entity_ids
        )
        for device_id in matched_devices:
            device = next(
                d for d in await coordinator.get_feeders() if d.api_name == device_id
            )
            if device is not None:
                await device.schedule_feed(time, amount, False)

    hass.services.async_register(DOMAIN, SERVICE_ADD_SCHEDULE, handle_add_schedule)

    async def handle_delete_schedule(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        time = call.data.get(ATTR_TIME)
        matched_devices = get_feeders_for_service(
            hass, area_ids, device_ids, entity_ids
        )

        for device_id in matched_devices:
            device = next(
                d for d in await coordinator.get_feeders() if d.api_name == device_id
            )
            if device is not None:
                schedules = await device.get_schedules()
                for schedule in schedules:
                    if schedule["time"] + ":00" == time:
                        await device.delete_schedule(str(schedule["id"]), False)
                        break

    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_SCHEDULE, handle_delete_schedule
    )

    async def handle_delete_all_schedules(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        matched_devices = get_feeders_for_service(
            hass, area_ids, device_ids, entity_ids
        )

        for device_id in matched_devices:
            device = next(
                d for d in await coordinator.get_feeders() if d.api_name == device_id
            )
            if device is not None:
                await device.delete_all_schedules(False)

    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_ALL_SCHEDULES, handle_delete_all_schedules
    )

    async def handle_modify_schedule(call: ServiceCall):
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        time = call.data.get(ATTR_TIME)
        amount = call.data.get(ATTR_AMOUNT)
        matched_devices = get_feeders_for_service(
            hass, area_ids, device_ids, entity_ids
        )

        for device_id in matched_devices:
            device = next(
                d for d in await coordinator.get_feeders() if d.api_name == device_id
            )
            if device is not None:
                schedules = await device.get_schedules()
                for schedule in schedules:
                    if schedule["time"] + ":00" == time:
                        await device.modify_schedule(
                            schedule["time"], amount, str(schedule["id"]), False
                        )
                        break

    hass.services.async_register(
        DOMAIN, SERVICE_MODIFY_SCHEDULE, handle_modify_schedule
    )

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
        self._feeders = None
        self._litterboxes = None
        self._device_lock = asyncio.Lock()

    async def get_feeders(self):
        async with self._device_lock:
            try:
                if self._feeders is None:
                    self._feeders = await self.api.get_feeders()
            except httpx.HTTPStatusError as ex:
                if ex.response.status_code in (401, 403):
                    await self.entry.async_start_reauth(self.hass)
                else:
                    raise
            return self._feeders

    async def get_litterboxes(self):
        async with self._device_lock:
            try:
                if self._litterboxes is None:
                    self._litterboxes = await self.api.get_litterboxes()
            except httpx.HTTPStatusError as ex:
                if ex.response.status_code in (401, 403):
                    await self.entry.async_start_reauth(self.hass)
                else:
                    raise
            return self._litterboxes

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            async with self._device_lock:
                self._feeders = await self.api.get_feeders()
                self._litterboxes = await self.api.get_litterboxes()
                return PetSafeData(self._feeders, self._litterboxes)
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code in (401, 403):
                raise ConfigEntryAuthFailed() from ex
            else:
                raise
