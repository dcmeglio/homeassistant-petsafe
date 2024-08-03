"""The PetSafe Integration integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import httpx
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_AREA_ID,
    ATTR_DEVICE_ID,
    ATTR_ENTITY_ID,
    CONF_ACCESS_TOKEN,
    CONF_EMAIL,
    CONF_TOKEN,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

import petsafe

from .const import (
    ATTR_AMOUNT,
    ATTR_SLOW_FEED,
    ATTR_TIME,
    CONF_REFRESH_TOKEN,
    DOMAIN,
    SERVICE_ADD_SCHEDULE,
    SERVICE_DELETE_ALL_SCHEDULES,
    SERVICE_DELETE_SCHEDULE,
    SERVICE_FEED,
    SERVICE_MODIFY_SCHEDULE,
    SERVICE_PRIME,
)
from .helpers import get_feeders_for_service

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
        client = get_async_client(hass)
    )

    hass.data.setdefault(DOMAIN, {})

    coordinator = PetSafeCoordinator(hass, client, entry)

    hass.data[DOMAIN][entry.entry_id] = coordinator

    async def handle_add_schedule(call: ServiceCall) -> None:
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

    async def handle_delete_schedule(call: ServiceCall) -> None:
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

    async def handle_delete_all_schedules(call: ServiceCall) -> None:
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

    async def handle_modify_schedule(call: ServiceCall) -> None:
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

    async def handle_feed(call: ServiceCall) -> None:
        device_ids = call.data.get(ATTR_DEVICE_ID)
        area_ids = call.data.get(ATTR_AREA_ID)
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        amount = call.data.get(ATTR_AMOUNT)
        slow_feed = call.data.get(ATTR_SLOW_FEED)
        matched_devices = get_feeders_for_service(
            hass, area_ids, device_ids, entity_ids
        )

        for device_id in matched_devices:
            device = next(
                d for d in await coordinator.get_feeders() if d.api_name == device_id
            )
            if device is not None:
                await device.feed(amount, slow_feed, False)
                await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_FEED, handle_feed)

    async def handle_prime(call: ServiceCall) -> None:
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
                # NB: DeviceSmartFeed.prime() synchronously updates state after priming.
                # Directly send a 5/8 cup meal here so that we can defer the update.
                await device.feed(5, False, False)
                await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_PRIME, handle_prime)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await coordinator.async_config_entry_first_refresh()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class PetSafeData:
    def __init__(
        self,
        feeders: list[petsafe.devices.DeviceSmartFeed],
        litterboxes: list[petsafe.devices.DeviceScoopfree],
    ):
        self.feeders = feeders
        self.litterboxes = litterboxes


class PetSafeCoordinator(DataUpdateCoordinator):
    """Data Update Coordinator for petsafe devices."""

    def __init__(
        self, hass: HomeAssistant, api: petsafe.PetSafeClient, entry: ConfigEntry
    ):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="PetSafe",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self.api: petsafe.PetSafeClient = api
        self.hass: HomeAssistant = hass
        self._feeders: list[petsafe.devices.DeviceSmartFeed] = None
        self._litterboxes: list[petsafe.devices.DeviceScoopfree] = None
        self._device_lock = asyncio.Lock()
        self.entry = entry

    async def get_feeders(self) -> list[petsafe.devices.DeviceSmartFeed]:
        """Return the list of feeders."""
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

    async def get_litterboxes(self) -> list[petsafe.devices.DeviceScoopfree]:
        """Return the list of litterboxes."""
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

    async def _async_update_data(self) -> PetSafeData:
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
                raise UpdateFailed() from ex
        except Exception as ex:
            raise UpdateFailed() from ex
