from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import EntityCategory

from . import PetSafeCoordinator, SelectEntities
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, add_entities):
    coordinator: PetSafeCoordinator = hass.data[DOMAIN][config.entry_id]

    litterboxes = None
    try:
        litterboxes = await coordinator.get_litterboxes()
    except Exception as ex:
        raise ConfigEntryNotReady(
            "Failed to retrieve PetSafe scoopfree devices"
        ) from ex

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
