"""NSW Fuel Station integration - setup and config flow."""

from __future__ import annotations

import logging
from typing import Any

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
    DEFAULT_FUEL_TYPES,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DOMAIN,
    FUEL_TYPES,
)

_LOGGER = logging.getLogger(__name__)


# Known station names (discovered via FuelCheck nearby API)
KNOWN_STATIONS: dict[int, str] = {
    20067: "Ampol Rousehill",
    20656: "7-Eleven Rouse Hill",
    20557: "OTR Rouse Hill",
    1268: "Independent Riverstone",
}


def _resolve_station_name(station_id: int) -> str:
    """Try to get station name from known stations or nearby lookup."""
    return KNOWN_STATIONS.get(station_id, f"Station {station_id}")


class NSWFuelStationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NSW Fuel Station."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            station_id = str(user_input[CONF_STATION_ID]).strip()
            fuel_types = user_input.get(CONF_FUEL_TYPES, DEFAULT_FUEL_TYPES)

            await self.async_set_unique_id(f"nsw_fuel_{station_id}")
            self._abort_if_unique_id_configured()

            station_name = _resolve_station_name(int(station_id))

            # Validate by fetching data
            try:
                client = FuelCheckClient()
                await self.hass.async_add_executor_job(
                    lambda: client.get_fuel_prices_for_station(station_id)
                )
            except Exception:
                _LOGGER.warning("Could not fetch initial data for %s (%s)", station_name, station_id)

            return self.async_create_entry(
                title=station_name,
                data={
                    CONF_STATION_ID: station_id,
                    CONF_STATION_NAME: station_name,
                },
                options={CONF_FUEL_TYPES: fuel_types},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION_ID): str,
                    vol.Optional(CONF_FUEL_TYPES, default=DEFAULT_FUEL_TYPES): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=FUEL_TYPES,
                            multiple=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return NSWFuelStationOptionsFlow(config_entry)


class NSWFuelStationOptionsFlow(OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(CONF_FUEL_TYPES, DEFAULT_FUEL_TYPES)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_FUEL_TYPES, default=current): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=FUEL_TYPES,
                            multiple=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )