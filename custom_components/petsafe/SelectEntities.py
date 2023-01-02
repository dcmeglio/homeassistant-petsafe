from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

import petsafe

from . import PetSafeData
from .const import DOMAIN, MANUFACTURER


class PetSafeSelectEntity(CoordinatorEntity, SelectEntity):
    def __init__(
        self,
        hass,
        api_name,
        name,
        coordinator,
        device_type,
        options,
        icon=None,
        device_class=None,
        entity_category=None,
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
        self._attr_options = options


class PetSafeLitterboxSelectEntity(PetSafeSelectEntity):
    def __init__(
        self,
        hass,
        name,
        coordinator,
        device_type,
        device: petsafe.devices.DeviceScoopfree,
        options,
        icon=None,
        device_class=None,
        entity_category=None,
    ):
        self._litterbox = device

        super().__init__(
            hass,
            device.api_name,
            name,
            coordinator,
            device_type,
            options,
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
        self._attr_current_option = None

    def _handle_coordinator_update(self) -> None:
        data: PetSafeData = self.coordinator.data
        litterbox: petsafe.devices.DeviceScoopfree = next(
            x for x in data.litterboxes if x.api_name == self._api_name
        )
        if self._device_type == "rake_timer":
            self._attr_current_option = str(
                litterbox.data["shadow"]["state"]["reported"]["rakeDelayTime"]
            )
        self.async_write_ha_state()
        return super()._handle_coordinator_update()

    async def async_select_option(self, option: str) -> None:
        if self._device_type == "rake_timer":
            await self._litterbox.modify_timer(int(option), False)
        await self._coordinator.async_request_refresh()
