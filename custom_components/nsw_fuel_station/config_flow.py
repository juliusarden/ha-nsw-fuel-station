"""NSW Fuel Station integration - setup and config flow."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from nsw_fuel import FuelCheckClient

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_FUEL_TYPES,
    CONF_STATION_ID,
    DEFAULT_FUEL_TYPES,
    DOMAIN,
    FUEL_TYPES,
)
from .coordinator import NSWFuelStationCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NSW Fuel Station from a config entry."""
    client = FuelCheckClient()
    coordinator = NSWFuelStationCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


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

            # Check if already configured
            await self.async_set_unique_id(f"nsw_fuel_{station_id}")
            self._abort_if_unique_id_configured()

            # Validate the station by trying to fetch data
            try:
                client = FuelCheckClient()
                prices = await self.hass.async_add_executor_job(
                    lambda: client.get_fuel_prices_for_station(station_id)
                )
            except Exception:
                prices = None

            # We don't strictly require prices to exist yet — the coordinator
            # will handle transient failures gracefully
            if prices is None:
                _LOGGER.warning("Could not fetch initial data for station %s", station_id)

            return self.async_create_entry(
                title=f"Fuel Station {station_id}",
                data={CONF_STATION_ID: station_id},
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
        """Initialize options flow."""
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