from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from . import PetSafeCoordinator, SwitchEntities
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, config, add_entities):
    coordinator: PetSafeCoordinator = hass.data[DOMAIN][config.entry_id]
    feeders = await coordinator.get_feeders()

    entities = []
    for feeder in feeders:
        entities.append(
            SwitchEntities.PetSafeFeederSwitchEntity(
                hass=hass,
                name="Feeding Paused",
                device_type="feeding_paused",
                icon="mdi:pause",
                device=feeder,
                coordinator=coordinator,
                entity_category=EntityCategory.CONFIG,
            )
        )
        entities.append(
            SwitchEntities.PetSafeFeederSwitchEntity(
                hass=hass,
                name="Child Lock",
                device_type="child_lock",
                icon="mdi:lock-open",
                device=feeder,
                coordinator=coordinator,
                entity_category=EntityCategory.CONFIG,
            )
        )
        entities.append(
            SwitchEntities.PetSafeFeederSwitchEntity(
                hass=hass,
                name="Slow Feed",
                device_type="slow_feed",
                icon="mdi:tortoise",
                device=feeder,
                coordinator=coordinator,
                entity_category=EntityCategory.CONFIG,
            )
        )
    add_entities(entities)
