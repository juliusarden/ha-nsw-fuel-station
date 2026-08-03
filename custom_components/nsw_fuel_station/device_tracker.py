"""Device tracker platform — shows station location on HA map with fuel prices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_FUEL_TYPES, CONF_STATION_ID, CONF_STATION_LAT, CONF_STATION_LON, CONF_STATION_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker for station location."""
    station_id = entry.data.get(CONF_STATION_ID, "0")
    station_name = entry.data.get(CONF_STATION_NAME, f"Station {station_id}")
    lat = entry.data.get(CONF_STATION_LAT, 0)
    lon = entry.data.get(CONF_STATION_LON, 0)

    if lat and lon:
        coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        fuel_types = entry.options.get(CONF_FUEL_TYPES, [])
        async_add_entities([NSWFuelStationTracker(station_name, station_id, lat, lon, coordinator, fuel_types)])


class NSWFuelStationTracker(TrackerEntity):
    """Device tracker showing station on map with fuel prices in popup."""

    _attr_has_entity_name = True
    _attr_source_type = SourceType.GPS
    _attr_icon = "mdi:gas-station"

    def __init__(
        self,
        station_name: str,
        station_id: str,
        lat: float,
        lon: float,
        coordinator=None,
        fuel_types=None,
    ) -> None:
        self._station_name = station_name
        self._station_id = station_id
        self._coordinator = coordinator
        self._fuel_types = set(fuel_types or [])
        self._attr_name = station_name
        self._attr_latitude = lat
        self._attr_longitude = lon
        self._attr_unique_id = f"nsw_fuel_loc_{station_id}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = {
            "station_name": self._station_name,
            "station_id": self._station_id,
        }
        if self._coordinator and self._coordinator.data:
            prices = self._coordinator.data.get("prices", {})
            for fuel_type, data in sorted(prices.items()):
                # Only show user-selected fuel types (or all if none selected)
                if self._fuel_types and fuel_type not in self._fuel_types:
                    continue
                price = data.get("price")
                if price is not None:
                    attrs[f"price_{fuel_type}"] = f"{price}¢/L"
        return attrs

    async def async_added_to_hass(self) -> None:
        """Listen to coordinator updates."""
        if self._coordinator:
            self.async_on_remove(
                self._coordinator.async_add_listener(self.async_write_ha_state)
            )