import time
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
import petsafe
import datetime
from .const import (
    CAT_IN_BOX,
    DOMAIN,
    ERROR_SENSOR_BLOCKED,
    MANUFACTURER,
    RAKE_BUTTON_DETECTED,
    RAKE_FINISHED,
    RAKE_NOW,
)
from . import PetSafeData
import pytz


class PetSafeSensorEntity(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        hass,
        api_name,
        name,
        coordinator,
        device_type,
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
        self._attr_unique_id = api_name + "_" + device_type
        self._attr_icon = icon
        self._device_type = device_type
        self._attr_entity_category = entity_category


class PetSafeLitterboxSensorEntity(PetSafeSensorEntity):
    def __init__(
        self,
        hass,
        name,
        coordinator,
        device_type,
        device: petsafe.devices.DeviceScoopfree,
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
            icon,
            device_class,
            entity_category,
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.api_name)},
            manufacturer=MANUFACTURER,
            name=device.friendly_name,
            model=device.data["productName"],
            sw_version=device.data["shadow"]["state"]["reported"]["firmware"],
        )

        if self._device_type == "last_cleaning" or self._device_type == "rake_status":
            self._attr_should_poll = True
        else:
            self._attr_should_poll = False

    def _handle_coordinator_update(self) -> None:
        data: PetSafeData = self.coordinator.data
        litterbox: petsafe.devices.DeviceScoopfree = next(
            x for x in data.litterboxes if x.api_name == self._api_name
        )
        if self._device_type == "rake_counter":
            self._attr_native_value = litterbox.data["shadow"]["state"]["reported"][
                "rakeCount"
            ]
        elif self._device_type == "signal_strength":
            self._attr_native_value = litterbox.data["shadow"]["state"]["reported"][
                "rssi"
            ]
        if self._attr_should_poll:
            self.schedule_update_ha_state(True)
        else:
            self.async_write_ha_state()
        return super()._handle_coordinator_update()

    async def async_update(self) -> None:

        if self._device_type == "last_cleaning":
            data: PetSafeData = self.coordinator.data
            litterbox: petsafe.devices.DeviceScoopfree = next(
                x for x in data.litterboxes if x.api_name == self._api_name
            )
            events = await self.hass.async_add_executor_job(litterbox.get_activity)
            reversed_events = reversed(events["data"])
            for item in reversed_events:
                if item["payload"]["code"] == RAKE_FINISHED:
                    self._attr_native_value = datetime.datetime.fromtimestamp(
                        int(item["payload"]["timestamp"]) / 1000, pytz.timezone("UTC")
                    )
                    break
        elif self._device_type == "rake_status":
            data: PetSafeData = self.coordinator.data
            litterbox: petsafe.devices.DeviceScoopfree = next(
                x for x in data.litterboxes if x.api_name == self._api_name
            )
            events = await self.hass.async_add_executor_job(litterbox.get_activity)
            reversed_events = reversed(events["data"])
            status = None
            for item in reversed_events:
                code = item["payload"]["code"]
                if code == RAKE_FINISHED:
                    status = "idle"
                    break
                elif code == CAT_IN_BOX:
                    status = "timing"
                    timestamp = int(item["payload"]["timestamp"]) / 1000
                    rake_timer_in_seconds = (
                        litterbox.data["shadow"]["state"]["reported"]["rakeDelayTime"]
                        * 60
                    )
                    if timestamp + rake_timer_in_seconds >= time.time():
                        status = "raking"
                    break
                elif code == RAKE_BUTTON_DETECTED or code == RAKE_NOW:
                    status = "raking"
                    break
                elif code == ERROR_SENSOR_BLOCKED:
                    status = "jammed"
                    break
            self._attr_native_value = status

        return await super().async_update()


class PetSafeFeederSensorEntity(PetSafeSensorEntity):
    def __init__(
        self,
        hass,
        name,
        coordinator,
        device_type,
        device: petsafe.devices.DeviceSmartFeed,
        icon=None,
        device_class=None,
        entity_category=None,
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
            sw_version=device.data["firmware_version"],
            model=device.data["product_name"],
        )

        if self._device_type == "last_feeding":
            self._attr_should_poll = True
        else:
            self._attr_should_poll = False

    def _handle_coordinator_update(self) -> None:
        data: PetSafeData = self.coordinator.data
        feeder: petsafe.devices.DeviceSmartFeed = next(
            x for x in data.feeders if x.api_name == self._api_name
        )
        if self._device_type == "battery":
            self._attr_native_value = feeder.battery_level
        elif self._device_type == "food_level":
            if feeder.food_low_status == 0:
                status = "full"
            elif feeder.food_low_status == 1:
                status = "low"
            else:
                status = "empty"
            self._attr_native_value = status
        elif self._device_type == "signal_strength":
            self._attr_native_value = feeder.data["network_rssi"]

        if self._attr_should_poll:
            self.schedule_update_ha_state(True)
        else:
            self.async_write_ha_state()
        return super()._handle_coordinator_update()

    async def async_update(self) -> None:

        if self._device_type == "last_feeding":
            data: PetSafeData = self.coordinator.data
            feeder: petsafe.devices.DeviceSmartFeed = next(
                x for x in data.feeders if x.api_name == self._api_name
            )
            test = await self.hass.async_add_executor_job(feeder.get_messages_since)
            feeding = await self.hass.async_add_executor_job(feeder.get_last_feeding)
            self._attr_native_value = datetime.datetime.fromtimestamp(
                feeding["payload"]["time"], pytz.timezone("UTC")
            )

        return await super().async_update()
