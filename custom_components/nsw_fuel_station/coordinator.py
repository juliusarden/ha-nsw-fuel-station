"""Data coordinator for NSW Fuel Station."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from nsw_fuel import FuelCheckClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_STATION_ID, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class NSWFuelStationCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch fuel prices."""

    def __init__(
        self, hass: HomeAssistant, client: FuelCheckClient, entry: ConfigEntry
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.station_id = str(entry.data[CONF_STATION_ID])
        self._entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.station_id}",
            update_interval=timedelta(minutes=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch fuel prices from the API."""
        try:
            prices = await self.hass.async_add_executor_job(
                lambda: self.client.get_fuel_prices_for_station(self.station_id)
            )
        except Exception as err:
            raise UpdateFailed(f"Error fetching data for station {self.station_id}: {err}") from err

        if not prices:
            raise UpdateFailed(f"No data returned for station {self.station_id}")

        # Return structured data keyed by fuel type
        # Price objects use attributes, not dict keys
        result = {}
        for p in prices:
            fuel_type = getattr(p, "fuel_type", "")
            if fuel_type:
                result[fuel_type] = {
                    "price": getattr(p, "price", None),
                    "fuel_type": fuel_type,
                    "last_updated": getattr(p, "last_updated", None),
                }
        return result