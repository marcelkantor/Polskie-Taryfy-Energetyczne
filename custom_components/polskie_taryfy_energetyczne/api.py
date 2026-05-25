"""API client for Polskie Taryfy Energetyczne."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DISTRIBUTION_RATE,
    CONF_FIXED_MONTHLY_FEE,
    CONF_HIGH_RATE,
    CONF_LOW_RATE,
    CONF_OPERATOR,
    CONF_TARIFF,
    CONF_TAX_RATE,
    CONF_USE_CUSTOM_RATES,
    PRICE_ZONE_HIGH,
    PRICE_ZONE_LOW,
    PRICE_ZONE_SINGLE,
    TARIFF_G11,
    TARIFF_G12W,
)


@dataclass(slots=True, frozen=True)
class PTEForecastPoint:
    """Single forecast point."""

    start: datetime
    end: datetime
    price: Decimal
    price_zone: str


@dataclass(slots=True, frozen=True)
class PTETariffData:
    """Tariff data returned by the coordinator."""

    current_price: Decimal
    distribution_rate: Decimal
    fixed_monthly_fee: Decimal
    tax_rate: Decimal
    tariff: str
    operator: str
    current_price_zone: str
    next_price_zone_change: datetime | None
    forecast: list[PTEForecastPoint]
    fetched_at: datetime


class PTEApiClient:
    """Small API wrapper.

    Replace `_async_fetch_remote_prices` with a provider-specific implementation when
    the data source is selected. The current manual-rate path keeps the integration
    useful for fixed and manually entered tariffs.
    """

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the API client."""
        self._hass = hass
        self._config = config
        self._session = async_get_clientsession(hass)

    async def async_get_prices(self) -> PTETariffData:
        """Fetch current tariff data and forecast."""
        if not self._config.get(CONF_USE_CUSTOM_RATES, True):
            remote_data = await self._async_fetch_remote_prices()
            if remote_data is not None:
                return remote_data

        return self._build_custom_rate_data()

    async def _async_fetch_remote_prices(self) -> PTETariffData | None:
        """Fetch data from a remote source.

        This skeleton intentionally does not assume one official Polish pricing API.
        A future implementation can use `self._session` here for operator APIs,
        RCE/RDN data sources, or vendor-specific forecast services.
        """
        _ = self._session
        return None

    def _build_custom_rate_data(self) -> PTETariffData:
        """Build data from user-provided rates."""
        now = dt_util.utcnow()
        tariff = self._config.get(CONF_TARIFF, TARIFF_G11)
        high_rate = Decimal(str(self._config.get(CONF_HIGH_RATE, 0)))
        low_rate = Decimal(str(self._config.get(CONF_LOW_RATE, high_rate)))
        distribution_rate = Decimal(str(self._config.get(CONF_DISTRIBUTION_RATE, 0)))
        fixed_monthly_fee = Decimal(str(self._config.get(CONF_FIXED_MONTHLY_FEE, 0)))
        tax_rate = Decimal(str(self._config.get(CONF_TAX_RATE, 23)))

        forecast: list[PTEForecastPoint] = []
        for offset in range(24):
            start = now.replace(minute=0, second=0, microsecond=0) + timedelta(
                hours=offset
            )
            end = start + timedelta(hours=1)
            forecast.append(
                PTEForecastPoint(
                    start=start,
                    end=end,
                    price=self._select_rate_for_time(
                        tariff,
                        start,
                        high_rate,
                        low_rate,
                    ),
                    price_zone=self._select_price_zone_for_time(tariff, start),
                )
            )

        current_price_zone = self._select_price_zone_for_time(tariff, now)
        return PTETariffData(
            current_price=self._select_rate_for_time(tariff, now, high_rate, low_rate),
            distribution_rate=distribution_rate,
            fixed_monthly_fee=fixed_monthly_fee,
            tax_rate=tax_rate,
            tariff=tariff,
            operator=self._config[CONF_OPERATOR],
            current_price_zone=current_price_zone,
            next_price_zone_change=self._find_next_price_zone_change(
                tariff,
                now,
                current_price_zone,
            ),
            forecast=forecast,
            fetched_at=now,
        )

    @staticmethod
    def _select_rate_for_time(
        tariff: str,
        moment: datetime,
        high_rate: Decimal,
        low_rate: Decimal,
    ) -> Decimal:
        """Return the active energy rate for a tariff and timestamp."""
        price_zone = PTEApiClient._select_price_zone_for_time(tariff, moment)
        if price_zone == PRICE_ZONE_LOW:
            return low_rate
        return high_rate

    @staticmethod
    def _select_price_zone_for_time(tariff: str, moment: datetime) -> str:
        """Return the active price zone for a tariff and timestamp."""
        local = dt_util.as_local(moment)
        hour = local.hour

        if tariff == TARIFF_G11:
            return PRICE_ZONE_SINGLE

        is_low_late_window = hour < 6 or hour >= 22
        is_low_afternoon_window = 13 <= hour < 15
        is_weekend = local.weekday() >= 5

        if tariff == TARIFF_G12W and is_weekend:
            return PRICE_ZONE_LOW

        if is_low_late_window or is_low_afternoon_window:
            return PRICE_ZONE_LOW

        return PRICE_ZONE_HIGH

    @staticmethod
    def _find_next_price_zone_change(
        tariff: str,
        moment: datetime,
        current_price_zone: str,
    ) -> datetime | None:
        """Find the next price zone change within the next 48 hours."""
        if current_price_zone == PRICE_ZONE_SINGLE:
            return None

        start = moment.replace(second=0, microsecond=0)
        for offset in range(1, 48 * 60 + 1):
            candidate = start + timedelta(minutes=offset)
            if (
                PTEApiClient._select_price_zone_for_time(tariff, candidate)
                != current_price_zone
            ):
                return candidate

        return None
