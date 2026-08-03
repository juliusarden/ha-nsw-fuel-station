"""Binary sensor platform — compares station price vs NSW daily average."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_FUEL_TYPES, DEFAULT_FUEL_TYPES, DOMAIN
from .coordinator import NSWFuelAverageCoordinator, NSWFuelStationCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up comparison binary sensors."""
    station_coordinator: NSWFuelStationCoordinator = hass.data[DOMAIN][entry.entry_id]
    fuel_types = entry.options.get(CONF_FUEL_TYPES, DEFAULT_FUEL_TYPES)
    station_name = station_coordinator.station_name

    avg_coordinator = hass.data.get(f"{DOMAIN}_averages")
    if avg_coordinator is None:
        _LOGGER.warning("NSW average coordinator not yet available")
        async_add_entities([])
        return

    entities = []
    for fuel_type in fuel_types:
        entities.append(
            NSWFuelComparisonSensor(
                avg_coordinator, station_coordinator, station_name, fuel_type
            )
        )

    async_add_entities(entities)


class NSWFuelComparisonSensor(BinarySensorEntity):
    """ON = station price is BELOW NSW average (good deal)."""

    _attr_icon = "mdi:cash-check"

    def __init__(
        self,
        avg_coordinator: NSWFuelAverageCoordinator,
        station_coordinator: NSWFuelStationCoordinator,
        station_name: str,
        fuel_type: str,
    ) -> None:
        self.avg_coordinator = avg_coordinator
        self.station_coordinator = station_coordinator
        self._fuel_type = fuel_type
        self._station_id = station_coordinator.station_id
        self._station_name = station_name

        short = station_name.split(" ")[0]
        self._attr_unique_id = f"nsw_fuel_cmp_{self._station_id}_{fuel_type.lower()}"
        self._attr_name = f"{short} {fuel_type} below avg"
        self._attr_icon = "mdi:trending-down"

    @property
    def is_on(self) -> bool | None:
        if not self.station_coordinator.data or not self.avg_coordinator.data:
            return None
        sp = self.station_coordinator.data.get("prices", {}).get(self._fuel_type, {})
        nsw_avg = self.avg_coordinator.data.get(self._fuel_type)
        if not sp or nsw_avg is None:
            return None
        price = sp.get("price")
        if price is None:
            return None
        return float(price) < float(nsw_avg)

    @property
    def available(self) -> bool:
        return self.station_coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = {
            "station_name": self._station_name,
            "fuel_type": self._fuel_type,
        }
        if self.station_coordinator.data:
            p = self.station_coordinator.data.get("prices", {}).get(self._fuel_type, {})
            attrs["station_price"] = p.get("price")
        if self.avg_coordinator.data:
            attrs["nsw_average"] = self.avg_coordinator.data.get(self._fuel_type)
        return attrs

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self.station_coordinator.async_add_listener(self.async_write_ha_state)
        )
        self.async_on_remove(
            self.avg_coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        await self.station_coordinator.async_request_refresh()
        await self.avg_coordinator.async_request_refresh()