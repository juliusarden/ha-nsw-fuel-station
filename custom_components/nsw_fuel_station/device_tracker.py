"""Device tracker platform — shows station location on HA map."""

from __future__ import annotations

import logging

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_STATION_ID, CONF_STATION_LAT, CONF_STATION_LON, CONF_STATION_NAME, DOMAIN

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
        async_add_entities([NSWFuelStationTracker(station_name, station_id, lat, lon)])


class NSWFuelStationTracker(TrackerEntity):
    """Device tracker for a fuel station location."""

    _attr_has_entity_name = True
    _attr_source_type = SourceType.GPS
    _attr_icon = "mdi:gas-station"
    _attr_name = "Location"

    def __init__(self, station_name: str, station_id: str, lat: float, lon: float) -> None:
        self._station_name = station_name
        self._station_id = station_id
        self._attr_latitude = lat
        self._attr_longitude = lon
        short = station_name.split(" ")[0]
        self._attr_unique_id = f"nsw_fuel_loc_{station_id}"

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "station_name": self._station_name,
            "station_id": self._station_id,
        }