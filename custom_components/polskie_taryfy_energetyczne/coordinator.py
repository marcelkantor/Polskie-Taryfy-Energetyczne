"""Data update coordinator for Polskie Taryfy Energetyczne."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

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
        self._unsub_zone_refresh: CALLBACK_TYPE | None = None

    async def _async_update_data(self) -> PTETariffData:
        """Fetch data from API endpoint."""
        try:
            data = await self.client.async_get_prices()
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Could not update tariff data: {err}") from err
        self._schedule_next_price_zone_refresh(data)
        return data

    def _schedule_next_price_zone_refresh(self, data: PTETariffData) -> None:
        """Schedule an extra refresh at the next tariff zone boundary."""
        if self._unsub_zone_refresh is not None:
            self._unsub_zone_refresh()
            self._unsub_zone_refresh = None

        if data.next_price_zone_change is None:
            return

        delay = (
            data.next_price_zone_change - dt_util.utcnow()
        ).total_seconds() + 1
        if delay <= 0:
            return

        def _refresh_at_zone_change(_now) -> None:
            self._unsub_zone_refresh = None
            self.hass.async_create_task(self.async_request_refresh())

        self._unsub_zone_refresh = async_call_later(
            self.hass,
            delay,
            _refresh_at_zone_change,
        )

    def async_cancel_zone_refresh(self) -> None:
        """Cancel the scheduled tariff zone refresh."""
        if self._unsub_zone_refresh is not None:
            self._unsub_zone_refresh()
            self._unsub_zone_refresh = None
