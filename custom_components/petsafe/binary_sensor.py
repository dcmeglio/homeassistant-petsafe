from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import PetSafeCoordinator, PetSafeData
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
import petsafe
from .const import DOMAIN, MANUFACTURER
from . import BinarySensorEntities


async def async_setup_entry(hass: HomeAssistant, config, add_entities):
    coordinator: PetSafeCoordinator = hass.data[DOMAIN][config.entry_id]
    api: petsafe.PetSafeClient = coordinator.api

    feeders = await hass.async_add_executor_job(petsafe.devices.get_feeders, api)

    entities = []
    for feeder in feeders:
        entities.append(
            BinarySensorEntities.PetSafeFeederBinarySensorEntity(
                hass=hass,
                name="Feeding Paused",
                device_type="feeding_paused",
                icon="mdi:pause",
                device=feeder,
                coordinator=coordinator,
            )
        )
        entities.append(
            BinarySensorEntities.PetSafeFeederBinarySensorEntity(
                hass=hass,
                name="Child Lock",
                device_type="child_lock",
                icon="mdi:lock-open",
                device=feeder,
                coordinator=coordinator,
            )
        )
    add_entities(entities)
