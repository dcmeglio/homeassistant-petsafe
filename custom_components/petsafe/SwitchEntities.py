from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

import petsafe

from . import PetSafeCoordinator, PetSafeData
from .const import DOMAIN, MANUFACTURER


class PetSafeSwitchEntity(CoordinatorEntity, SwitchEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        api_name: str,
        name: str,
        coordinator: PetSafeCoordinator,
        device_type: str,
        icon: str = None,
        device_class: str = None,
        entity_category: str = None,
    ):
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_has_entity_name = True
        self._coordinator = coordinator
        self._api_name = api_name
        self._attr_should_poll = True
        self._attr_unique_id = api_name + "_" + device_type
        self._attr_icon = icon
        self._device_type = device_type
        self._attr_entity_category = entity_category


class PetSafeLitterboxSwitchEntity(PetSafeSwitchEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        coordinator: PetSafeCoordinator,
        device_type: str,
        device: petsafe.devices.DeviceScoopfree,
        icon: str = None,
        device_class: str = None,
        entity_category: str = None,
    ):
        self._litterbox = device

        super().__init__(
            hass,
            device.api_name,
            name,
            coordinator,
            device_type,
            icon,
            device_class,
            entity_category,
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.api_name)},
            manufacturer=MANUFACTURER,
            name=device.friendly_name,
            model=device.product_name,
            sw_version=device.firmware,
        )

    def _handle_coordinator_update(self) -> None:
        data: PetSafeData = self.coordinator.data
        litterbox: petsafe.devices.DeviceScoopfree = next(
            x for x in data.litterboxes if x.api_name == self._api_name
        )

        self.async_write_ha_state()
        return super()._handle_coordinator_update()


class PetSafeFeederSwitchEntity(PetSafeSwitchEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        coordinator: PetSafeCoordinator,
        device_type: str,
        device: petsafe.devices.DeviceSmartFeed,
        icon: str = None,
        device_class: str = None,
        entity_category: str = None,
    ):
        self._feeder = device

        super().__init__(
            hass,
            device.api_name,
            name,
            coordinator,
            device_type,
            icon,
            device_class,
            entity_category,
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.api_name)},
            manufacturer=MANUFACTURER,
            name=device.friendly_name,
            sw_version=device.firmware,
            model=device.product_name,
        )
        self._device = device

    def _handle_coordinator_update(self) -> None:
        data: PetSafeData = self.coordinator.data
        feeder: petsafe.devices.DeviceSmartFeed = next(
            x for x in data.feeders if x.api_name == self._api_name
        )
        if self._device_type == "child_lock":
            self._attr_is_on = feeder.is_locked
        elif self._device_type == "feeding_paused":
            self._attr_is_on = feeder.is_paused
        elif self._device_type == "slow_feed":
            self._attr_is_on = feeder.is_slow_feed

        self.schedule_update_ha_state(True)
        return super()._handle_coordinator_update()

    async def async_update(self) -> None:
        return await super().async_update()

    async def async_turn_on(self, **kwargs: Any) -> None:
        if self._device_type == "child_lock":
            await self._device.lock(True)
        elif self._device_type == "feeding_paused":
            await self._device.pause(True)
        elif self._device_type == "slow_feed":
            await self._device.slow_feed(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self._device_type == "child_lock":
            await self._device.lock(False)
        elif self._device_type == "feeding_paused":
            await self._device.pause(False)
        elif self._device_type == "slow_feed":
            await self._device.slow_feed(False)
