"""Data coordinator for NSW Fuel Station — station prices + NSW averages."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from nsw_fuel import FuelCheckClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DOMAIN,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class NSWFuelStationCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch fuel prices for a single station."""

    def __init__(
        self, hass: HomeAssistant, client: FuelCheckClient, entry: ConfigEntry
    ) -> None:
        self.client = client
        self.station_id = int(entry.data[CONF_STATION_ID])
        self.station_name = entry.options.get(
            CONF_STATION_NAME, entry.data.get(CONF_STATION_NAME, f"Station {self.station_id}")
        )
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
            raise UpdateFailed(
                f"Error fetching data for {self.station_name}: {err}"
            ) from err

        if not prices:
            raise UpdateFailed(f"No data returned for {self.station_name}")

        result = {
            "station_name": self.station_name,
            "station_id": self.station_id,
            "prices": {},
        }
        for p in prices:
            fuel_type = getattr(p, "fuel_type", "")
            if fuel_type:
                result["prices"][fuel_type] = {
                    "price": getattr(p, "price", None),
                    "fuel_type": fuel_type,
                    "last_updated": getattr(p, "last_updated", None),
                }
        return result


class NSWFuelAverageCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch NSW daily average prices by fuel type."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: FuelCheckClient,
        latitude: float = DEFAULT_LATITUDE,
        longitude: float = DEFAULT_LONGITUDE,
    ) -> None:
        self.client = client
        self.latitude = latitude
        self.longitude = longitude

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_averages",
            update_interval=timedelta(minutes=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch NSW daily average fuel prices."""
        fuel_types = ["E10", "U91", "P95", "P98", "DL", "PDL", "LPG"]
        result: dict[str, Any] = {}

        for fuel_type in fuel_types:
            try:
                trends = await self.hass.async_add_executor_job(
                    lambda ft=fuel_type: self.client.get_fuel_price_trends(
                        self.latitude, self.longitude, [ft]
                    )
                )
                # Find day period average
                for avg in trends.average_prices:
                    if getattr(avg, "period", None) and str(avg.period) == "Period.DAY":
                        result[fuel_type] = getattr(avg, "price", None)
                        break
            except Exception as err:
                _LOGGER.debug("Could not fetch NSW average for %s: %s", fuel_type, err)

        return result