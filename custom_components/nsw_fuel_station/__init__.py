"""NSW Fuel Station custom integration for Home Assistant.

A better implementation of the NSW Fuel Station integration with:
- UI config flow (add stations from Settings > Integrations)
- Per-station config entries
- Graceful handling of unavailable fuel types
- Individual sensor entities per fuel type per station
"""

import logging

from nsw_fuel import FuelCheckClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_STATION_ID, DOMAIN
from .coordinator import NSWFuelStationCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NSW Fuel Station from a config entry."""
    client = FuelCheckClient()
    coordinator = NSWFuelStationCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)