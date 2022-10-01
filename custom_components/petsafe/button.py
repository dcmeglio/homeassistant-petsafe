from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import PetSafeCoordinator, PetSafeData
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
import petsafe
from .const import DOMAIN, MANUFACTURER
from . import ButtonEntities


async def async_setup_entry(hass: HomeAssistant, config, add_entities):
    coordinator: PetSafeCoordinator = hass.data[DOMAIN]
    api: petsafe.PetSafeClient = coordinator.api

    feeders = await hass.async_add_executor_job(petsafe.devices.get_feeders, api)
    litterboxes = await hass.async_add_executor_job(
        petsafe.devices.get_litterboxes, api
    )

    entities = []
    for feeder in feeders:
        entities.append(
            ButtonEntities.PetSafeFeederButtonEntity(
                hass=hass,
                name="Feed",
                device_type="feed",
                device=feeder,
                coordinator=coordinator,
            )
        )
    for litterbox in litterboxes:
        entities.append(
            ButtonEntities.PetSafeLitterboxButtonEntity(
                hass=hass,
                name="Clean",
                device_type="clean",
                device=litterbox,
                coordinator=coordinator,
            )
        )
        entities.append(
            ButtonEntities.PetSafeLitterboxButtonEntity(
                hass=hass,
                name="Reset",
                device_type="reset",
                device=litterbox,
                coordinator=coordinator,
            )
        )
    add_entities(entities)
