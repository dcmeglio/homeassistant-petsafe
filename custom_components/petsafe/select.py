from . import PetSafeCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
import petsafe
from .const import DOMAIN
from . import SelectEntities


async def async_setup_entry(hass: HomeAssistant, config, add_entities):
    coordinator: PetSafeCoordinator = hass.data[DOMAIN][config.entry_id]
    api: petsafe.PetSafeClient = coordinator.api

    litterboxes = await hass.async_add_executor_job(
        petsafe.devices.get_litterboxes, api
    )

    entities = []
    for litterbox in litterboxes:
        entities.append(
            SelectEntities.PetSafeLitterboxSelectEntity(
                hass=hass,
                name="Rake Timer",
                device_type="rake_timer",
                device=litterbox,
                coordinator=coordinator,
                options=["5", "10", "15", "20", "25", "30"],
                entity_category=EntityCategory.CONFIG,
            )
        )
    add_entities(entities)
