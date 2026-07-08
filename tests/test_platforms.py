"""Platform-level tests for Control4 entity creation and base entity behavior."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.control4 import light, switch, binary_sensor
from custom_components.control4.const import (
    CONF_CONTROLLER_UNIQUE_ID,
    CONF_DIRECTOR,
    CONF_DIRECTOR_ALL_ITEMS,
    CONF_DYNAMIC_DEVICE_CALLBACKS,
    CONTROL4_ENTITY_TYPE,
)

CONTROLLER_UID = "C4-SR260_C4-SR260_001122334455"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry_data(all_items=None):
    """Minimal entry.runtime_data dict with mocked director and websocket."""
    director = AsyncMock()
    director.get_item_variables = AsyncMock(return_value=[])
    director.get_item_setup = AsyncMock(return_value={})
    return {
        CONF_DIRECTOR: director,
        CONF_CONTROLLER_UNIQUE_ID: CONTROLLER_UID,
        CONF_DYNAMIC_DEVICE_CALLBACKS: [],
        CONF_DIRECTOR_ALL_ITEMS: all_items or [],
    }


def _make_entry(entry_data):
    """Minimal mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.runtime_data = entry_data
    entry.options = {}
    return entry


def _capture_add_entities():
    """Return (callback, list) where list collects every entity passed to the callback."""
    entities = []

    def add_entities(entity_list, update_before_add=False):
        entities.extend(entity_list)

    return add_entities, entities


# ---------------------------------------------------------------------------
# Light platform
# ---------------------------------------------------------------------------

LIGHT_PARENT = {
    "id": 10,
    "name": "Lutron Switch",
    "manufacturer": "Lutron",
    "model": "RR-2RLD",
    "type": 8,  # driver type, not CONTROL4_ENTITY_TYPE
    "proxy": "light_v2",
    "roomName": "Living Room",
    "parentId": 0,
}

LIGHT_ITEM = {
    "id": 100,
    "name": "Living Room Light",
    "type": CONTROL4_ENTITY_TYPE,
    "proxy": "light_v2",
    "roomName": "Living Room",
    "parentId": 10,
}

FAN_ITEM = {
    "id": 200,
    "name": "Ceiling Fan",
    "type": CONTROL4_ENTITY_TYPE,
    "proxy": "fan",
    "roomName": "Bedroom",
    "parentId": 10,
}


async def test_light_setup_creates_entity(hass):
    """Light platform creates an entity for each non-fan light item."""
    entry_data = _make_entry_data()
    entry_data[CONF_DIRECTOR].get_item_variables = AsyncMock(
        return_value=[{"varName": "Level", "value": 75}]
    )
    entry = _make_entry(entry_data)
    add_entities, added = _capture_add_entities()

    with patch(
        "custom_components.control4.light.get_items_of_category",
        AsyncMock(return_value=[LIGHT_PARENT, LIGHT_ITEM]),
    ):
        await light.async_setup_entry(hass, entry, add_entities)

    assert len(added) == 1
    entity = added[0]
    assert entity._attr_name == "Living Room Light"
    assert entity._idx == 100
    assert entity._device_manufacturer == "Lutron"
    assert entity._device_model == "RR-2RLD"


async def test_light_excludes_fan_proxy(hass):
    """Items with proxy='fan' are not created as light entities."""
    entry_data = _make_entry_data()
    entry = _make_entry(entry_data)
    add_entities, added = _capture_add_entities()

    with patch(
        "custom_components.control4.light.get_items_of_category",
        AsyncMock(return_value=[LIGHT_PARENT, FAN_ITEM]),
    ):
        await light.async_setup_entry(hass, entry, add_entities)

    assert added == []


async def test_light_registers_dynamic_callback(hass):
    """async_setup_entry registers a dynamic-device callback."""
    entry_data = _make_entry_data()
    entry = _make_entry(entry_data)
    add_entities, _ = _capture_add_entities()

    with patch(
        "custom_components.control4.light.get_items_of_category",
        AsyncMock(return_value=[]),
    ):
        await light.async_setup_entry(hass, entry, add_entities)

    assert len(entry_data[CONF_DYNAMIC_DEVICE_CALLBACKS]) == 1


# ---------------------------------------------------------------------------
# Switch platform
# ---------------------------------------------------------------------------

RELAY_ITEM = {
    "id": 300,
    "name": "Pool Pump",
    "type": CONTROL4_ENTITY_TYPE,
    "proxy": "relaysingle_relay_c4",
    "roomName": "Outdoors",
    "parentId": 30,
    "manufacturer": "Control4",
    "model": "C4-SR260",
}

PUMP_RELAY_ITEM = {
    "id": 301,
    "name": "Spa Pump",
    "type": CONTROL4_ENTITY_TYPE,
    "proxy": "relaysingle_pump_c4",
    "roomName": "Outdoors",
    "parentId": 30,
    "manufacturer": "Control4",
    "model": "C4-SR260",
}


async def test_switch_creates_relay_entity(hass):
    """Switch platform creates an entity for relay items that expose RelayState."""
    entry_data = _make_entry_data(all_items=[RELAY_ITEM])
    entry_data[CONF_DIRECTOR].get_item_variables = AsyncMock(
        return_value=[{"varName": "RelayState", "value": 0}]
    )
    entry = _make_entry(entry_data)
    add_entities, added = _capture_add_entities()

    await switch.async_setup_entry(hass, entry, add_entities)

    assert len(added) == 1
    assert added[0]._attr_name == "Pool Pump"
    assert added[0]._idx == 300


async def test_switch_skips_item_without_relay_state(hass):
    """Switch platform skips items where director returns no RelayState variable."""
    entry_data = _make_entry_data(all_items=[RELAY_ITEM])
    # director returns no variables for this item
    entry_data[CONF_DIRECTOR].get_item_variables = AsyncMock(return_value=[])
    entry = _make_entry(entry_data)
    add_entities, added = _capture_add_entities()

    await switch.async_setup_entry(hass, entry, add_entities)

    assert added == []


async def test_switch_excludes_non_relay_items(hass):
    """Items with a non-relay proxy are ignored by the switch platform."""
    non_relay = {**LIGHT_ITEM, "id": 400, "proxy": "light_v2"}
    entry_data = _make_entry_data(all_items=[non_relay])
    entry = _make_entry(entry_data)
    add_entities, added = _capture_add_entities()

    await switch.async_setup_entry(hass, entry, add_entities)

    assert added == []


# ---------------------------------------------------------------------------
# Binary sensor platform
# ---------------------------------------------------------------------------

DOOR_SENSOR_ITEM = {
    "id": 500,
    "name": "Front Door",
    "type": CONTROL4_ENTITY_TYPE,
    "proxy": "contactsingle_doorcontactsensor_c4",
    "roomName": "Entryway",
    "parentId": 50,
    "manufacturer": "Control4",
    "model": "DS-Door",
}

BS_PARENT = {
    "id": 50,
    "name": "DS-Door Driver",
    "manufacturer": "Control4",
    "model": "DS-Door",
    "type": 8,
    "proxy": "contactsingle_doorcontactsensor_c4",
    "roomName": "Entryway",
    "parentId": 0,
}


async def test_binary_sensor_creates_door_entity(hass):
    """Binary sensor platform creates an entity for a door contact sensor."""
    entry_data = _make_entry_data(all_items=[BS_PARENT, DOOR_SENSOR_ITEM])
    entry_data[CONF_DIRECTOR].get_item_variables = AsyncMock(
        return_value=[{"varName": "ContactState", "value": 0}]
    )
    entry_data[CONF_DIRECTOR].get_item_setup = AsyncMock(return_value={})
    entry = _make_entry(entry_data)
    add_entities, added = _capture_add_entities()

    with patch(
        "custom_components.control4.binary_sensor.get_items_of_category",
        AsyncMock(return_value=[BS_PARENT, DOOR_SENSOR_ITEM]),
    ):
        await binary_sensor.async_setup_entry(hass, entry, add_entities)

    assert any(e._idx == 500 for e in added)
    door = next(e for e in added if e._idx == 500)
    assert door._attr_name == "Front Door"


async def test_binary_sensor_skips_relay_proxies(hass):
    """Binary sensor platform ignores items with relay proxies (handled by switch)."""
    relay_item = {**DOOR_SENSOR_ITEM, "proxy": "relaysingle_relay_c4"}
    entry_data = _make_entry_data(all_items=[relay_item])
    entry = _make_entry(entry_data)
    add_entities, added = _capture_add_entities()

    with patch(
        "custom_components.control4.binary_sensor.get_items_of_category",
        AsyncMock(return_value=[relay_item]),
    ):
        await binary_sensor.async_setup_entry(hass, entry, add_entities)

    assert not any(e._idx == DOOR_SENSOR_ITEM["id"] for e in added)


# ---------------------------------------------------------------------------
# Entity base class: log-when-unavailable behavior
# ---------------------------------------------------------------------------

def _make_light_entity(entry_data=None, entry=None):
    """Instantiate a Control4Light without registering it with hass."""
    if entry_data is None:
        entry_data = _make_entry_data()
    if entry is None:
        entry = _make_entry(entry_data)
    entity = light.Control4Light(
        entry_data,
        entry,
        "Test Light",
        100,
        "Device Name",
        "Manufacturer",
        "Model",
        10,
        "Room",
        {"Level": 50},
    )
    entity.async_write_ha_state = MagicMock()
    return entity


async def test_entity_logs_warning_on_first_unavailable(caplog):
    """_update_callback logs a warning the first time an entity becomes unavailable."""
    entity = _make_light_entity()
    assert entity._attr_available is True or entity._attr_available is None or getattr(entity, "_attr_available", True)

    with caplog.at_level(logging.WARNING, logger="custom_components.control4"):
        await entity._update_callback(100, False)

    assert entity._attr_available is False
    assert "unavailable" in caplog.text.lower()


async def test_entity_does_not_relog_while_still_unavailable(caplog):
    """Subsequent unavailable callbacks do not produce duplicate log entries."""
    entity = _make_light_entity()

    with caplog.at_level(logging.WARNING, logger="custom_components.control4"):
        await entity._update_callback(100, False)

    caplog.clear()

    with caplog.at_level(logging.WARNING, logger="custom_components.control4"):
        await entity._update_callback(100, False)

    assert "unavailable" not in caplog.text.lower()


async def test_entity_logs_info_on_recovery(caplog):
    """_update_callback logs info when entity recovers from unavailable."""
    entity = _make_light_entity()

    # First mark unavailable
    await entity._update_callback(100, False)
    caplog.clear()

    # Recover
    with caplog.at_level(logging.INFO, logger="custom_components.control4"):
        await entity._update_callback(100, {"evtName": "OnDataToUI", "data": {}})

    assert entity._attr_available is True
    assert "available again" in caplog.text.lower()


async def test_entity_does_not_log_recovery_if_already_available(caplog):
    """No recovery log is emitted when the entity was never unavailable."""
    entity = _make_light_entity()
    entity._attr_available = True
    caplog.clear()

    with caplog.at_level(logging.INFO, logger="custom_components.control4"):
        await entity._update_callback(100, {"evtName": "OnDataToUI", "data": {}})

    assert "available again" not in caplog.text.lower()
