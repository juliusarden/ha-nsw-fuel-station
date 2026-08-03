"""NSW Fuel Station integration - config flow with suburb search."""

from __future__ import annotations

import logging
from typing import Any

import requests
import voluptuous as vol
from nsw_fuel import FuelCheckClient

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_FUEL_TYPES,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_STATION_LAT,
    CONF_STATION_LON,
    DEFAULT_FUEL_TYPES,
    DOMAIN,
    FUEL_TYPES,
)

_LOGGER = logging.getLogger(__name__)

PHOTON_URL = "https://photon.komoot.io/api/"
FUEL_API_BASE = "https://api.onegov.nsw.gov.au/FuelCheckApp/v1"
SEARCH_RADIUS = 15  # km


def _geocode_suburb(suburb: str) -> tuple[float, float] | None:
    """Convert suburb name to lat/long using Photon."""
    try:
        resp = requests.get(
            PHOTON_URL,
            params={"q": f"{suburb} NSW Australia", "limit": 1},
            timeout=8,
            headers={"User-Agent": "ha-nsw-fuel-station/1.0"},
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
        if features:
            coords = features[0]["geometry"]["coordinates"]
            return (coords[1], coords[0])
    except Exception as exc:
        _LOGGER.debug("Geocoding failed: %s", exc)
    return None


def _search_nearby_stations(lat: float, lon: float) -> list[dict[str, Any]]:
    """Search nearby stations with coordinates via raw FuelCheck API."""
    from datetime import datetime
    try:
        resp = requests.post(
            f"{FUEL_API_BASE}/fuel/prices/nearby",
            json={
                "fueltype": "U91",
                "latitude": lat,
                "longitude": lon,
                "radius": SEARCH_RADIUS,
                "brand": [],
            },
            headers={"requesttimestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")},
            timeout=12,
        )
        resp.raise_for_status()
        data = resp.json()
        stations = {}
        for s in data.get("stations", []):
            code = s.get("code", 0)
            loc = s.get("location", {})
            stations[code] = {
                "code": str(code),
                "name": s.get("name", ""),
                "brand": s.get("brand", ""),
                "address": s.get("address", ""),
                "latitude": loc.get("latitude", lat),
                "longitude": loc.get("longitude", lon),
            }
        return list(stations.values())
    except Exception as exc:
        _LOGGER.warning("Station search failed: %s", exc)
        return []


class NSWFuelStationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NSW Fuel Station."""

    VERSION = 2

    def __init__(self) -> None:
        super().__init__()
        self._station_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Initial step — choose search or manual."""
        if user_input is not None:
            if user_input["method"] == "search":
                return await self.async_step_search()
            return await self.async_step_manual()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("method", default="search"): vol.In({
                    "search": "Search by suburb",
                    "manual": "Enter station ID manually",
                })
            }),
        )

    async def async_step_search(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Search for stations by suburb name."""
        errors = {}

        if user_input is not None:
            suburb = user_input.get("suburb", "").strip()
            if not suburb:
                errors["suburb"] = "suburb_required"
            else:
                coords = await self.hass.async_add_executor_job(_geocode_suburb, suburb)
                if not coords:
                    errors["suburb"] = "geocode_failed"
                else:
                    stations = await self.hass.async_add_executor_job(
                        _search_nearby_stations, coords[0], coords[1]
                    )
                    if not stations:
                        errors["suburb"] = "no_stations"
                    else:
                        self._station_data["stations"] = stations
                        return await self.async_step_select_station()

        return self.async_show_form(
            step_id="search",
            data_schema=vol.Schema({vol.Required("suburb"): str}),
            errors=errors,
        )

    async def async_step_select_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Pick a station from search results."""
        stations = self._station_data.get("stations", [])

        if user_input is not None:
            selected_code = user_input["station"]
            station = next((s for s in stations if s["code"] == selected_code), None)
            if station:
                await self.async_set_unique_id(f"nsw_fuel_{station['code']}")
                self._abort_if_unique_id_configured()

                self._station_data["station_id"] = station["code"]
                self._station_data["station_name"] = station["name"]
                self._station_data["station_lat"] = station["latitude"]
                self._station_data["station_lon"] = station["longitude"]
                return await self.async_step_fuel_types()

        options = {
            s["code"]: f"{s['brand']} — {s['name']} ({s.get('address','')[:30]})"
            for s in stations
        }
        return self.async_show_form(
            step_id="select_station",
            data_schema=vol.Schema({vol.Required("station"): vol.In(options)}),
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manual station ID entry."""
        if user_input is not None:
            station_id = str(user_input[CONF_STATION_ID]).strip()
            await self.async_set_unique_id(f"nsw_fuel_{station_id}")
            self._abort_if_unique_id_configured()
            self._station_data["station_id"] = station_id
            self._station_data["station_name"] = f"Station {station_id}"
            self._station_data["station_lat"] = 0
            self._station_data["station_lon"] = 0
            return await self.async_step_fuel_types()

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({vol.Required(CONF_STATION_ID): str}),
        )

    async def async_step_fuel_types(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Pick fuel types and create entry."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._station_data["station_name"],
                data={
                    CONF_STATION_ID: self._station_data["station_id"],
                    CONF_STATION_NAME: self._station_data["station_name"],
                    CONF_STATION_LAT: self._station_data.get("station_lat", 0),
                    CONF_STATION_LON: self._station_data.get("station_lon", 0),
                },
                options={
                    CONF_FUEL_TYPES: user_input.get(CONF_FUEL_TYPES, DEFAULT_FUEL_TYPES),
                },
            )

        return self.async_show_form(
            step_id="fuel_types",
            data_schema=vol.Schema({
                vol.Optional(CONF_FUEL_TYPES, default=DEFAULT_FUEL_TYPES): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=FUEL_TYPES, multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return NSWFuelStationOptionsFlow(config_entry)


class NSWFuelStationOptionsFlow(OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self._config_entry.options.get(CONF_FUEL_TYPES, DEFAULT_FUEL_TYPES)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_FUEL_TYPES, default=current): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=FUEL_TYPES, multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )