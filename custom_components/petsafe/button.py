from homeassistant.core import HomeAssistant

from . import ButtonEntities, PetSafeCoordinator
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, config, add_entities):
    coordinator: PetSafeCoordinator = hass.data[DOMAIN][config.entry_id]

    feeders = await coordinator.get_feeders()
    litterboxes = await coordinator.get_litterboxes()

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
