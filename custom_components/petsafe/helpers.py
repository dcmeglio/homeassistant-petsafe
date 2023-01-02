from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.device_registry import DeviceEntry, DeviceRegistry

from .const import DOMAIN, FEEDER_MODEL


def get_feeders_for_service(hass: HomeAssistant, area_ids, device_ids, entity_ids):
    matched_devices = []

    if area_ids is not None:
        matched_devices = get_feeders_by_area_id(
            hass,
            device_registry.async_get(hass),
            entity_registry.async_get(hass),
            area_ids,
            matched_devices,
        )
    if device_ids is not None:
        matched_devices = get_feeders_by_device_id(
            hass, device_registry.async_get(hass), device_ids, matched_devices
        )

    if entity_ids is not None:
        matched_devices = get_feeders_by_entity_id(
            hass,
            device_registry.async_get(hass),
            entity_registry.async_get(hass),
            entity_ids,
            matched_devices,
        )
    return matched_devices


def get_feeders_by_area_id(
    hass: HomeAssistant,
    device_reg: DeviceRegistry,
    entity_reg: entity_registry.EntityRegistry,
    area_ids,
    matched_devices=[],
):
    for area_id in area_ids:
        devices = device_registry.async_entries_for_area(device_reg, area_id)
        device_ids = []
        [device_ids.append(x.id) for x in devices if x.id not in device_ids]
        entities = entity_registry.async_entries_for_area(entity_reg, area_id)
        entity_ids = []
        [entity_ids.append(x.id) for x in entities if x.id not in entity_ids]

        devices_from_registry = get_feeders_by_device_id(hass, device_reg, device_ids)

        [
            matched_devices.append(x)
            for x in devices_from_registry
            if x not in matched_devices
        ]

    return matched_devices


def get_feeders_by_device_id(
    hass: HomeAssistant, device_reg: DeviceRegistry, device_ids, matched_devices=[]
):
    for device_id in device_ids:
        device_entry = device_reg.async_get(device_id)

        if is_device_feeder(hass, device_entry):
            api_name = next(iter(device_entry.identifiers))[1]
            if not api_name in matched_devices:
                matched_devices.append(api_name)
    return matched_devices


def get_feeders_by_entity_id(
    hass: HomeAssistant,
    device_reg: DeviceRegistry,
    entity_reg: entity_registry.EntityRegistry,
    entity_ids,
    matched_devices=[],
):
    for entity_id in entity_ids:
        entity = entity_reg.async_get(entity_id)
        [
            matched_devices.append(x)
            for x in get_feeders_by_device_id(hass, device_reg, [entity.device_id])
            if x not in matched_devices
        ]
    return matched_devices


def is_device_feeder(hass: HomeAssistant, device: DeviceEntry):
    if device.model != FEEDER_MODEL:
        return False

    config_entry_ids = device.config_entries
    entry = next(
        (
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.entry_id in config_entry_ids
        ),
        None,
    )
    if entry and entry.state != ConfigEntryState.LOADED:
        return False
    if entry is None or entry.entry_id not in hass.data[DOMAIN]:
        return False

    return True
