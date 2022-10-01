from . import PetSafeCoordinator
from homeassistant.core import HomeAssistant
import petsafe
from .const import DOMAIN
from . import ButtonEntities


async def async_setup_entry(hass: HomeAssistant, config, add_entities):
    coordinator: PetSafeCoordinator = hass.data[DOMAIN][config.entry_id]
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
