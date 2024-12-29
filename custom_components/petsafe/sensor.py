from datetime import timedelta
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import EntityCategory

from . import PetSafeCoordinator, SensorEntities
from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, add_entities):
    coordinator: PetSafeCoordinator = hass.data[DOMAIN][config.entry_id]
    feeders = None
    litterboxes = None
    try:
        feeders = await coordinator.get_feeders()
        litterboxes = await coordinator.get_litterboxes()
    except Exception as ex:
        raise ConfigEntryNotReady("Failed to retrieve PetSafe devices") from ex

    entities = []
    for feeder in feeders:
        entities.append(
            SensorEntities.PetSafeFeederSensorEntity(
                hass=hass,
                name="Battery Level",
                device_class="battery",
                device_type="battery",
                device=feeder,
                coordinator=coordinator,
            )
        )
        entities.append(
            SensorEntities.PetSafeFeederSensorEntity(
                hass=hass,
                name="Last Feeding",
                device_type="last_feeding",
                device_class="timestamp",
                device=feeder,
                coordinator=coordinator,
            )
        )
        entities.append(
            SensorEntities.PetSafeFeederSensorEntity(
                hass=hass,
                name="Next Feeding",
                device_type="next_feeding",
                device_class="timestamp",
                device=feeder,
                coordinator=coordinator,
            )
        )
        entities.append(
            SensorEntities.PetSafeFeederSensorEntity(
                hass=hass,
                name="Food Level",
                device_type="food_level",
                device=feeder,
                coordinator=coordinator,
                icon="mdi:bowl",
            )
        )
        entities.append(
            SensorEntities.PetSafeFeederSensorEntity(
                hass=hass,
                name="Signal Strength",
                device_type="signal_strength",
                device=feeder,
                coordinator=coordinator,
                device_class="signal_strength",
                entity_category=EntityCategory.DIAGNOSTIC,
            )
        )
    for litterbox in litterboxes:
        entities.append(
            SensorEntities.PetSafeLitterboxSensorEntity(
                hass=hass,
                name="Rake Counter",
                device_type="rake_counter",
                device=litterbox,
                coordinator=coordinator,
                icon="mdi:rake",
            )
        )
        entities.append(
            SensorEntities.PetSafeLitterboxSensorEntity(
                hass=hass,
                name="Rake Status",
                device_type="rake_status",
                device=litterbox,
                coordinator=coordinator,
                icon="mdi:rake",
            )
        )
        entities.append(
            SensorEntities.PetSafeLitterboxSensorEntity(
                hass=hass,
                name="Signal Strength",
                device_type="signal_strength",
                device=litterbox,
                coordinator=coordinator,
                device_class="signal_strength",
                entity_category=EntityCategory.DIAGNOSTIC,
            )
        )
        entities.append(
            SensorEntities.PetSafeLitterboxSensorEntity(
                hass=hass,
                name="Last Cleaning",
                device_type="last_cleaning",
                device=litterbox,
                coordinator=coordinator,
                device_class="timestamp",
            )
        )
    add_entities(entities)
