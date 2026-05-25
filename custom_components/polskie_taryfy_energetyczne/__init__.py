"""Polskie Taryfy Energetyczne integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import PTEApiClient
from .const import DOMAIN
from .coordinator import PTEDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

type PTEConfigEntry = ConfigEntry[PTEDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PTEConfigEntry) -> bool:
    """Set up Polskie Taryfy Energetyczne from a config entry."""
    client = PTEApiClient(hass, entry.data | entry.options)
    coordinator = PTEDataUpdateCoordinator(hass, client, entry)

    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    entry.async_on_unload(entry.add_update_listener(async_update_options))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PTEConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_update_options(hass: HomeAssistant, entry: PTEConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
