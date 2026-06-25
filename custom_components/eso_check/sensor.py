"""Sensor platform for ESO Free Capacity Check."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_OBJECT_NUMBER, DOMAIN, STATE_AVAILABLE, STATE_NONE
from .coordinator import EsoCheckCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ESO sensor based on a config entry."""
    coordinator: EsoCheckCoordinator = entry.runtime_data
    async_add_entities([EsoFreeCapacitySensor(coordinator, entry)])


class EsoFreeCapacitySensor(CoordinatorEntity[EsoCheckCoordinator], SensorEntity):
    """Sensor reporting true when free capacity exists, none otherwise."""

    _attr_has_entity_name = True
    _attr_name = "Free capacity"
    _attr_icon = "mdi:solar-power"

    def __init__(self, coordinator: EsoCheckCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        object_number = entry.data[CONF_OBJECT_NUMBER]
        self._attr_unique_id = f"{entry.entry_id}_free_capacity"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "ESO",
            "model": "Laisvos galios pasitikrinimas",
        }
        self._attr_extra_state_attributes = {
            "object_number": object_number,
        }

    @property
    def native_value(self) -> str | None:
        """Return true when capacity is available, none when it is not."""
        if self.coordinator.data is None:
            return None

        if self.coordinator.data.get("has_free_capacity"):
            return STATE_AVAILABLE

        return STATE_NONE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional ESO response details."""
        data = self.coordinator.data or {}
        return {
            "object_number": data.get("object_number"),
            "message": data.get("message"),
            "messages": data.get("messages"),
            "capacities": data.get("capacities"),
        }
