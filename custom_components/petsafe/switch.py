from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import EntityCategory

from . import PetSafeCoordinator, SwitchEntities
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, add_entities):
    coordinator: PetSafeCoordinator = hass.data[DOMAIN][config.entry_id]

    feeders = None
    try:
        feeders = await coordinator.get_feeders()
    except Exception as ex:
        raise ConfigEntryNotReady(
            "Failed to retrieve PetSafe SmartFeed devices"
        ) from ex

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
