"""API client for Polskie Taryfy Energetyczne."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import quote

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ACTIVE_ENERGY_PRICE_ENTITY,
    CONF_G14_S1_RATE,
    CONF_G14_S2_RATE,
    CONF_G14_S3_RATE,
    CONF_G14_S4_RATE,
    CONF_HIGH_RATE,
    CONF_LOW_RATE,
    CONF_MEDIUM_RATE,
    CONF_PRESET_OPERATOR,
    CONF_PRICE_SOURCE,
    CONF_TARIFF,
    PRICE_SOURCE_CUSTOM,
    PRICE_SOURCE_PRESET,
    PRICE_ZONE_G14_S1,
    PRICE_ZONE_G14_S2,
    PRICE_ZONE_G14_S3,
    PRICE_ZONE_G14_S4,
    PRICE_ZONE_HIGH,
    PRICE_ZONE_LOW,
    PRICE_ZONE_MEDIUM,
    PRICE_ZONE_SINGLE,
    TARIFF_G13,
    TARIFF_G14DYNAMIC,
    TARIFF_G11,
    TARIFF_G12W,
)

PSE_PDGSZ_URL = "https://api.raporty.pse.pl/api/pdgsz"
G14_STATUS_TO_ZONE = {
    0: PRICE_ZONE_G14_S1,
    1: PRICE_ZONE_G14_S2,
    2: PRICE_ZONE_G14_S3,
    3: PRICE_ZONE_G14_S4,
}
G14_ZONE_TO_RATE_KEY = {
    PRICE_ZONE_G14_S1: PRICE_ZONE_G14_S1,
    PRICE_ZONE_G14_S2: PRICE_ZONE_G14_S2,
    PRICE_ZONE_G14_S3: PRICE_ZONE_G14_S3,
    PRICE_ZONE_G14_S4: PRICE_ZONE_G14_S4,
}


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
    current_distribution_price: Decimal | None
    current_active_energy_price: Decimal | None
    current_purchase_price: Decimal | None
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
        if self._config.get(CONF_TARIFF) == TARIFF_G14DYNAMIC:
            presets = await self._async_load_presets()
            if price_source == PRICE_SOURCE_CUSTOM:
                return await self._async_build_custom_g14dynamic_data(presets)
            return await self._async_build_g14dynamic_data(presets)
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

        price_type = tariff_data.get("price_type", presets["price_type"])
        high_rate = Decimal(str(prices.get(PRICE_ZONE_HIGH, prices.get("single", 0))))
        medium_rate = Decimal(str(prices.get(PRICE_ZONE_MEDIUM, high_rate)))
        low_rate = Decimal(str(prices.get(PRICE_ZONE_LOW, high_rate)))
        return self._build_tariff_data(
            high_rate=high_rate,
            medium_rate=medium_rate,
            low_rate=low_rate,
            price_source=PRICE_SOURCE_PRESET,
            price_type=price_type,
            preset_year=int(presets["year"]),
            source=tariff_data.get("source", presets["source"]),
            source_url=tariff_data.get(
                "source_url",
                presets["source_urls"][tariff.lower()],
            ),
            operator=operator,
        )

    async def _async_build_g14dynamic_data(
        self,
        presets: dict[str, Any],
    ) -> PTETariffData:
        """Build G14dynamic data from bundled rates and PSE schedule."""
        tariff = self._config.get(CONF_TARIFF, TARIFF_G14DYNAMIC)
        tariff_data = presets["tariffs"][tariff]
        preset_operator = self._config.get(CONF_PRESET_OPERATOR, "tauron")
        operator = (
            preset_operator
            if preset_operator in tariff_data["prices"]
            else "tauron"
        )
        prices = tariff_data["prices"][operator]
        return await self._async_build_g14dynamic_tariff_data(
            prices={
                PRICE_ZONE_G14_S1: Decimal(str(prices[PRICE_ZONE_G14_S1])),
                PRICE_ZONE_G14_S2: Decimal(str(prices[PRICE_ZONE_G14_S2])),
                PRICE_ZONE_G14_S3: Decimal(str(prices[PRICE_ZONE_G14_S3])),
                PRICE_ZONE_G14_S4: Decimal(str(prices[PRICE_ZONE_G14_S4])),
            },
            price_source=PRICE_SOURCE_PRESET,
            price_type=tariff_data.get("price_type", presets["price_type"]),
            preset_year=int(presets["year"]),
            source=tariff_data.get("source", presets["source"]),
            source_url=tariff_data.get(
                "source_url",
                presets["source_urls"][tariff.lower()],
            ),
            operator=operator,
        )

    async def _async_build_custom_g14dynamic_data(
        self,
        presets: dict[str, Any],
    ) -> PTETariffData:
        """Build G14dynamic data from user-provided rates and PSE schedule."""
        tariff = self._config.get(CONF_TARIFF, TARIFF_G14DYNAMIC)
        tariff_data = presets["tariffs"][tariff]
        return await self._async_build_g14dynamic_tariff_data(
            prices={
                PRICE_ZONE_G14_S1: Decimal(
                    str(self._config.get(CONF_G14_S1_RATE, 0))
                ),
                PRICE_ZONE_G14_S2: Decimal(
                    str(self._config.get(CONF_G14_S2_RATE, 0))
                ),
                PRICE_ZONE_G14_S3: Decimal(
                    str(self._config.get(CONF_G14_S3_RATE, 0))
                ),
                PRICE_ZONE_G14_S4: Decimal(
                    str(self._config.get(CONF_G14_S4_RATE, 0))
                ),
            },
            price_source=PRICE_SOURCE_CUSTOM,
            price_type=tariff_data.get("price_type", "gross_distribution_kwh"),
            preset_year=None,
            source=None,
            source_url=None,
            operator="custom",
        )

    async def _async_build_g14dynamic_tariff_data(
        self,
        prices: dict[str, Decimal],
        price_source: str,
        price_type: str,
        preset_year: int | None,
        source: str | None,
        source_url: str | None,
        operator: str,
    ) -> PTETariffData:
        """Build G14dynamic tariff data from rates and PSE schedule."""
        schedule = await self._async_fetch_g14dynamic_schedule()
        now = dt_util.utcnow()

        forecast = [
            PTEForecastPoint(
                start=point["start"],
                end=point["end"],
                price=prices[G14_ZONE_TO_RATE_KEY[point["price_zone"]]],
                price_zone=point["price_zone"],
            )
            for point in schedule
        ]

        current = next(
            (point for point in forecast if point.start <= now < point.end),
            forecast[0] if forecast else None,
        )
        if current is None:
            raise ValueError("PSE G14dynamic schedule is empty")

        active_energy_price = self._current_active_energy_price()
        return PTETariffData(
            current_price=current.price,
            current_distribution_price=current.price,
            current_active_energy_price=active_energy_price,
            current_purchase_price=(
                current.price + active_energy_price
                if active_energy_price is not None
                else None
            ),
            tariff=TARIFF_G14DYNAMIC,
            operator=operator,
            price_source=price_source,
            price_type=price_type,
            preset_year=preset_year,
            source=source,
            source_url=source_url,
            current_price_zone=current.price_zone,
            next_price_zone_change=_find_next_forecast_zone_change(
                forecast,
                now,
                current.price_zone,
            ),
            forecast=forecast,
            fetched_at=now,
        )

    async def _async_fetch_g14dynamic_schedule(self) -> list[dict[str, Any]]:
        """Fetch G14dynamic hourly schedule from PSE Energetyczny Kompas."""
        now = dt_util.now()
        days = [
            now.date(),
            (now + timedelta(days=1)).date(),
        ]
        session = async_get_clientsession(self._hass)
        entries: list[dict[str, Any]] = []

        for day in days:
            day_filter = quote(
                f"business_date eq '{day.isoformat()}' and is_active eq true",
                safe="",
            )
            url = f"{PSE_PDGSZ_URL}?$select=usage_fcst,dtime&$filter={day_filter}"
            async with session.get(url) as response:
                response.raise_for_status()
                payload = await response.json()
            entries.extend(payload.get("value", []))

        schedule: list[dict[str, Any]] = []
        for entry in sorted(entries, key=lambda item: item["dtime"]):
            zone = G14_STATUS_TO_ZONE.get(entry.get("usage_fcst"))
            if zone is None:
                continue
            start = dt_util.as_utc(
                datetime.strptime(entry["dtime"], "%Y-%m-%d %H:%M").replace(
                    tzinfo=dt_util.DEFAULT_TIME_ZONE
                )
            )
            schedule.append(
                {
                    "start": start,
                    "end": start + timedelta(hours=1),
                    "price_zone": zone,
                }
            )

        return [point for point in schedule if point["end"] > dt_util.utcnow()]

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
        current_price = self._select_rate_for_time(
            tariff,
            now,
            high_rate,
            medium_rate,
            low_rate,
        )
        return PTETariffData(
            current_price=current_price,
            current_distribution_price=None,
            current_active_energy_price=None,
            current_purchase_price=current_price,
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

    def _current_active_energy_price(self) -> Decimal | None:
        """Return current active energy price from an optional HA sensor."""
        entity_id = self._config.get(CONF_ACTIVE_ENERGY_PRICE_ENTITY)
        if entity_id is None:
            return None

        state = self._hass.states.get(entity_id)
        if state is None or state.state in {"unknown", "unavailable"}:
            return None

        try:
            return Decimal(str(state.state))
        except Exception:  # noqa: BLE001
            return None

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


def _find_next_forecast_zone_change(
    forecast: list[PTEForecastPoint],
    moment: datetime,
    current_price_zone: str,
) -> datetime | None:
    """Find the next price zone change in a fetched forecast."""
    for point in forecast:
        if point.end <= moment:
            continue
        if point.price_zone != current_price_zone:
            return point.start
    return None


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
