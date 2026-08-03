"""Sensor platform for NSW Fuel Station."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_CENT, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_FUEL_TYPES, DEFAULT_FUEL_TYPES, DOMAIN
from .coordinator import NSWFuelStationCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NSW Fuel Station sensors."""
    coordinator: NSWFuelStationCoordinator = hass.data[DOMAIN][entry.entry_id]
    fuel_types = entry.options.get(CONF_FUEL_TYPES, DEFAULT_FUEL_TYPES)

    entities = []
    for fuel_type in fuel_types:
        entities.append(
            NSWFuelPriceSensor(coordinator, entry, fuel_type)
        )

    async_add_entities(entities)


class NSWFuelPriceSensor(SensorEntity):
    """Sensor for a single fuel type at a station."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CURRENCY_CENT
    _attr_suggested_display_precision = 1
    _attr_has_entity_name = True
    _attr_translation_key = "fuel_price"

    def __init__(
        self,
        coordinator: NSWFuelStationCoordinator,
        entry: ConfigEntry,
        fuel_type: str,
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._fuel_type = fuel_type
        self._station_id = coordinator.station_id

        self._attr_unique_id = f"nsw_fuel_{self._station_id}_{fuel_type.lower()}"
        self._attr_name = fuel_type
        self._attr_icon = "mdi:gas-station"

    @property
    def native_value(self) -> float | None:
        """Return the current price."""
        if self.coordinator.data and self._fuel_type in self.coordinator.data:
            price = self.coordinator.data[self._fuel_type].get("price")
            if price is not None:
                try:
                    return float(price)
                except (TypeError, ValueError):
                    return None
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        # Entity is available even if this fuel type has no data
        # (station might not sell this fuel type)
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {
            "station_id": self._station_id,
            "fuel_type": self._fuel_type,
        }
        if self.coordinator.data and self._fuel_type in self.coordinator.data:
            attrs["last_updated"] = self.coordinator.data[self._fuel_type].get("last_updated")
        return attrs

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()