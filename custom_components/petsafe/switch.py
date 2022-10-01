from . import PetSafeCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
import petsafe
from .const import DOMAIN
from . import SwitchEntities


async def async_setup_entry(hass: HomeAssistant, config, add_entities):
    coordinator: PetSafeCoordinator = hass.data[DOMAIN][config.entry_id]
    api: petsafe.PetSafeClient = coordinator.api

    feeders = await hass.async_add_executor_job(petsafe.devices.get_feeders, api)

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
    add_entities(entities)
