"""Data update coordinator for Polskie Taryfy Energetyczne."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PTEApiClient, PTETariffData
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PTEDataUpdateCoordinator(DataUpdateCoordinator[PTETariffData]):
    """Coordinate tariff data fetching."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: PTEApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> PTETariffData:
        """Fetch data from API endpoint."""
        try:
            return await self.client.async_get_prices()
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Could not update tariff data: {err}") from err
