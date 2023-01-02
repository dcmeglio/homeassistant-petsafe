from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo
import petsafe
from .const import DOMAIN, MANUFACTURER
from . import PetSafeCoordinator


class PetSafeButtonEntity(CoordinatorEntity, ButtonEntity):
    def __init__(
        self,
        hass,
        api_name,
        name,
        coordinator: PetSafeCoordinator,
        device_type,
        icon=None,
        device_class=None,
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


class PetSafeLitterboxButtonEntity(PetSafeButtonEntity):
    def __init__(
        self,
        hass,
        name,
        coordinator: PetSafeCoordinator,
        device_type,
        device: petsafe.devices.DeviceScoopfree,
        icon=None,
        device_class=None,
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
        )
        self._device = device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.api_name)},
            manufacturer=MANUFACTURER,
            name=device.friendly_name,
            model=device.product_name,
            sw_version=device.firmware,
        )

    async def async_press(self) -> None:
        if self._device_type == "reset":
            await self._device.reset(0, False)
        elif self._device_type == "clean":
            await self._device.rake(False)
        await self.coordinator.async_request_refresh()


class PetSafeFeederButtonEntity(PetSafeButtonEntity):
    def __init__(
        self,
        hass,
        name,
        coordinator: PetSafeCoordinator,
        device_type,
        device: petsafe.devices.DeviceSmartFeed,
        icon=None,
        device_class=None,
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
        )

        self._device = device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.api_name)},
            manufacturer=MANUFACTURER,
            name=device.friendly_name,
            sw_version=device.firmware,
            model=device.product_name,
        )

    async def async_press(self) -> None:
        if self._device_type == "feed":
            await self._device.feed(1, None, False)
        await self.coordinator.async_request_refresh()
