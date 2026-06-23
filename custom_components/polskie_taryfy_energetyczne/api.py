"""API client for Polskie Taryfy Energetyczne."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HIGH_RATE,
    CONF_LOW_RATE,
    CONF_MEDIUM_RATE,
    CONF_PRESET_OPERATOR,
    CONF_PRICE_SOURCE,
    CONF_TARIFF,
    PRICE_SOURCE_CUSTOM,
    PRICE_SOURCE_PRESET,
    PRICE_ZONE_HIGH,
    PRICE_ZONE_LOW,
    PRICE_ZONE_MEDIUM,
    PRICE_ZONE_SINGLE,
    TARIFF_G13,
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
    tariff: str
    operator: str
    price_source: str
    price_type: str
    preset_year: int | None
    source: str | None
    source_url: str | None
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
        self._presets: dict[str, Any] | None = None

    async def async_get_prices(self) -> PTETariffData:
        """Fetch current tariff data and forecast."""
        price_source = self._config.get(CONF_PRICE_SOURCE, PRICE_SOURCE_PRESET)
        if price_source == PRICE_SOURCE_CUSTOM:
            return self._build_custom_rate_data()
        presets = await self._async_load_presets()
        return self._build_preset_data(presets)

    async def _async_load_presets(self) -> dict[str, Any]:
        """Load bundled presets outside the event loop."""
        if self._presets is None:
            self._presets = await self._hass.async_add_executor_job(_load_presets)
        return self._presets

    def _build_preset_data(self, presets: dict[str, Any]) -> PTETariffData:
        """Build tariff data from bundled gross price presets."""
        tariff = self._config.get(CONF_TARIFF, TARIFF_G11)
        preset_operator = self._config.get(CONF_PRESET_OPERATOR, "average")
        tariff_data = presets["tariffs"][tariff]
        operator = preset_operator if tariff_data["operator_required"] else "average"
        if operator not in tariff_data["prices"]:
            operator = next(iter(tariff_data["prices"]))
        prices = tariff_data["prices"][operator]

        high_rate = Decimal(str(prices.get(PRICE_ZONE_HIGH, prices.get("single", 0))))
        medium_rate = Decimal(str(prices.get(PRICE_ZONE_MEDIUM, high_rate)))
        low_rate = Decimal(str(prices.get(PRICE_ZONE_LOW, high_rate)))
        return self._build_tariff_data(
            high_rate=high_rate,
            medium_rate=medium_rate,
            low_rate=low_rate,
            price_source=PRICE_SOURCE_PRESET,
            price_type=presets["price_type"],
            preset_year=int(presets["year"]),
            source=tariff_data.get("source", presets["source"]),
            source_url=tariff_data.get(
                "source_url",
                presets["source_urls"][tariff.lower()],
            ),
            operator=operator,
        )

    def _build_custom_rate_data(self) -> PTETariffData:
        """Build data from user-provided rates."""
        high_rate = Decimal(str(self._config.get(CONF_HIGH_RATE, 0)))
        medium_rate = Decimal(str(self._config.get(CONF_MEDIUM_RATE, high_rate)))
        low_rate = Decimal(str(self._config.get(CONF_LOW_RATE, high_rate)))
        return self._build_tariff_data(
            high_rate=high_rate,
            medium_rate=medium_rate,
            low_rate=low_rate,
            price_source=PRICE_SOURCE_CUSTOM,
            price_type="gross_kwh",
            preset_year=None,
            source=None,
            source_url=None,
            operator="custom",
        )

    def _build_tariff_data(
        self,
        high_rate: Decimal,
        medium_rate: Decimal,
        low_rate: Decimal,
        price_source: str,
        price_type: str,
        preset_year: int | None,
        source: str | None,
        source_url: str | None,
        operator: str,
    ) -> PTETariffData:
        """Build common tariff data from gross rates."""
        now = dt_util.utcnow()
        tariff = self._config.get(CONF_TARIFF, TARIFF_G11)

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
                        medium_rate,
                        low_rate,
                    ),
                    price_zone=self._select_price_zone_for_time(tariff, start),
                )
            )

        current_price_zone = self._select_price_zone_for_time(tariff, now)
        return PTETariffData(
            current_price=self._select_rate_for_time(
                tariff,
                now,
                high_rate,
                medium_rate,
                low_rate,
            ),
            tariff=tariff,
            operator=operator,
            price_source=price_source,
            price_type=price_type,
            preset_year=preset_year,
            source=source,
            source_url=source_url,
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
        medium_rate: Decimal,
        low_rate: Decimal,
    ) -> Decimal:
        """Return the active energy rate for a tariff and timestamp."""
        price_zone = PTEApiClient._select_price_zone_for_time(tariff, moment)
        if price_zone == PRICE_ZONE_LOW:
            return low_rate
        if price_zone == PRICE_ZONE_MEDIUM:
            return medium_rate
        return high_rate

    @staticmethod
    def _select_price_zone_for_time(tariff: str, moment: datetime) -> str:
        """Return the active price zone for a tariff and timestamp."""
        local = dt_util.as_local(moment)
        hour = local.hour

        if tariff == TARIFF_G11:
            return PRICE_ZONE_SINGLE

        if tariff == TARIFF_G13:
            if _is_non_working_day(local.date()):
                return PRICE_ZONE_LOW

            is_summer = 4 <= local.month <= 9
            if 7 <= hour < 13:
                return PRICE_ZONE_MEDIUM
            if is_summer and 19 <= hour < 22:
                return PRICE_ZONE_HIGH
            if not is_summer and 16 <= hour < 21:
                return PRICE_ZONE_HIGH
            return PRICE_ZONE_LOW

        is_low_late_window = hour < 6 or hour >= 22
        is_low_afternoon_window = 13 <= hour < 15
        is_non_working_day = _is_non_working_day(local.date())

        if tariff == TARIFF_G12W and is_non_working_day:
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


def _load_presets() -> dict[str, Any]:
    """Load bundled gross price presets."""
    path = Path(__file__).with_name("data") / "presets_2026.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _is_non_working_day(day: date) -> bool:
    """Return true for weekends and Polish statutory public holidays."""
    if day.weekday() >= 5:
        return True

    easter = _easter_sunday(day.year)
    return day in {
        date(day.year, 1, 1),
        date(day.year, 1, 6),
        easter + timedelta(days=1),
        date(day.year, 5, 1),
        date(day.year, 5, 3),
        easter + timedelta(days=60),
        date(day.year, 8, 15),
        date(day.year, 11, 1),
        date(day.year, 11, 11),
        date(day.year, 12, 24),
        date(day.year, 12, 25),
        date(day.year, 12, 26),
    }


def _easter_sunday(year: int) -> date:
    """Calculate Easter Sunday date for Gregorian calendar."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    leaping = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * leaping) // 451
    month = (h + leaping - 7 * m + 114) // 31
    day = ((h + leaping - 7 * m + 114) % 31) + 1
    return date(year, month, day)
