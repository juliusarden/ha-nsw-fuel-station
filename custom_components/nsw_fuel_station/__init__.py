"""NSW Fuel Station custom integration for Home Assistant.

Features:
- Per-station fuel price sensors with station names
- NSW daily average price comparison (below/above avg)
- UI config flow for easy setup
"""

import logging

from nsw_fuel import FuelCheckClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import NSWFuelAverageCoordinator, NSWFuelStationCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NSW Fuel Station from a config entry."""
    client = FuelCheckClient()

    # Set up the NSW average coordinator once (shared across all stations)
    if f"{DOMAIN}_averages" not in hass.data:
        avg_coordinator = NSWFuelAverageCoordinator(hass, client)
        hass.data[f"{DOMAIN}_averages"] = avg_coordinator
        await avg_coordinator.async_config_entry_first_refresh()

    coordinator = NSWFuelStationCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)