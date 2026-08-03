"""Sensor platform for NSW Fuel Station — per-fuel price sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_CENT
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
    """Set up NSW Fuel Station price sensors."""
    coordinator: NSWFuelStationCoordinator = hass.data[DOMAIN][entry.entry_id]
    fuel_types = entry.options.get(CONF_FUEL_TYPES, DEFAULT_FUEL_TYPES)
    station_name = coordinator.station_name

    entities = []
    for fuel_type in fuel_types:
        entities.append(NSWFuelPriceSensor(coordinator, station_name, fuel_type))

    async_add_entities(entities)


class NSWFuelPriceSensor(SensorEntity):
    """Sensor for a single fuel type at a station."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = CURRENCY_CENT
    _attr_suggested_display_precision = 1
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NSWFuelStationCoordinator,
        station_name: str,
        fuel_type: str,
    ) -> None:
        self.coordinator = coordinator
        self._fuel_type = fuel_type
        self._station_id = coordinator.station_id
        self._station_name = station_name

        short = station_name.split(" ")[0]
        self._attr_unique_id = f"nsw_fuel_{self._station_id}_{fuel_type.lower()}"
        self._attr_name = f"{short} {fuel_type}"
        self._attr_icon = "mdi:gas-station"

    @property
    def native_value(self) -> float | None:
        prices = self.coordinator.data.get("prices", {}) if self.coordinator.data else {}
        if self._fuel_type in prices:
            p = prices[self._fuel_type].get("price")
            return float(p) if p is not None else None
        return None

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        prices = self.coordinator.data.get("prices", {}) if self.coordinator.data else {}
        attrs = {
            "station_name": self._station_name,
            "station_id": self._station_id,
            "fuel_type": self._fuel_type,
        }
        if self._fuel_type in prices:
            attrs["last_updated"] = prices[self._fuel_type].get("last_updated")
        return attrs

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()