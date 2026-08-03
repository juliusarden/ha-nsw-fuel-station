"""NSW Fuel Station custom integration for Home Assistant."""

import logging

from nsw_fuel import FuelCheckClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import NSWFuelAverageCoordinator, NSWFuelStationCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "device_tracker"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NSW Fuel Station from a config entry."""
    client = FuelCheckClient()

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
    """Unload a config entry, removing all associated entities."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    else:
        _LOGGER.warning("Failed to unload platforms for %s, forcing cleanup", entry.title)
        hass.data[DOMAIN].pop(entry.entry_id, None)
        unload_ok = True  # still allow reload to proceed
    return unload_ok


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change — entity list adapts to new fuel types."""
    _LOGGER.debug("Options changed for %s, reloading", entry.title)
    await hass.config_entries.async_reload(entry.entry_id)