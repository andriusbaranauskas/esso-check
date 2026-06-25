"""Binary sensor platform for ESO Free Capacity Check."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_OBJECT_NUMBER, DOMAIN
from .coordinator import EsoCheckCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ESO binary sensor based on a config entry."""
    coordinator: EsoCheckCoordinator = entry.runtime_data
    async_add_entities([EsoFreeCapacityBinarySensor(coordinator, entry)])


class EsoFreeCapacityBinarySensor(
    CoordinatorEntity[EsoCheckCoordinator], BinarySensorEntity
):
    """Binary sensor: on when ESO returns an allowed XKW value."""

    _attr_has_entity_name = True
    _attr_name = "Free capacity available"
    _attr_icon = "mdi:solar-power"

    def __init__(self, coordinator: EsoCheckCoordinator, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        object_number = entry.data[CONF_OBJECT_NUMBER]
        self._attr_unique_id = f"{entry.entry_id}_free_capacity_binary"
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
    def is_on(self) -> bool | None:
        """Return True when ESO allows application with a kW limit."""
        if self.coordinator.data is None:
            return None

        return bool(self.coordinator.data.get("allowed_kw_value"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional ESO response details."""
        data = self.coordinator.data or {}
        return {
            "object_number": data.get("object_number"),
            "allowed_kw_value": data.get("allowed_kw_value"),
            "message": data.get("message"),
            "messages": data.get("messages"),
            "capacities": data.get("capacities"),
        }
