"""Sensors for Polskie Taryfy Energetyczne."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .api import PTETariffData
from .const import (
    ATTR_FETCHED_AT,
    ATTR_FORECAST,
    ATTR_OPERATOR,
    ATTR_PRICE_ZONE,
    ATTR_PRICE_SOURCE,
    ATTR_PRICE_TYPE,
    ATTR_PRESET_YEAR,
    ATTR_SOURCE,
    ATTR_SOURCE_URL,
    ATTR_TARIFF,
    CONF_ENERGY_ENTITY,
    CONF_TARIFF,
    CREATOR,
    DEFAULT_NAME,
    DOMAIN,
)
from .coordinator import PTEDataUpdateCoordinator

PRICE_UNIT = "PLN/kWh"
CURRENCY = "PLN"
PRICE_PRECISION = Decimal("0.01")
MINUTE_PRECISION = Decimal("0.1")


@dataclass(frozen=True, kw_only=True)
class PTESensorEntityDescription(SensorEntityDescription):
    """Describes PTE sensor entity."""

    value_fn: Callable[[PTETariffData, HomeAssistant, ConfigEntry], Any]
    attrs_fn: Callable[[PTETariffData], dict[str, Any]] | None = None


def _base_attrs(data: PTETariffData) -> dict[str, Any]:
    """Return common state attributes."""
    return {
        ATTR_OPERATOR: data.operator,
        ATTR_TARIFF: data.tariff,
        ATTR_PRICE_ZONE: data.current_price_zone,
        ATTR_PRICE_SOURCE: data.price_source,
        ATTR_PRICE_TYPE: data.price_type,
        ATTR_PRESET_YEAR: data.preset_year,
        ATTR_SOURCE: data.source,
        ATTR_SOURCE_URL: data.source_url,
        ATTR_FETCHED_AT: data.fetched_at.isoformat(),
        "next_price_zone_change": (
            data.next_price_zone_change.isoformat()
            if data.next_price_zone_change is not None
            else None
        ),
    }


def _forecast_attrs(data: PTETariffData) -> dict[str, Any]:
    """Return compact forecast attributes."""
    attrs = _base_attrs(data)
    attrs[ATTR_FORECAST] = [
        {
            "start": point.start.isoformat(),
            "end": point.end.isoformat(),
            "price": float(_round_price(point.price)),
            "price_zone": point.price_zone,
        }
        for point in data.forecast
    ]
    return attrs


def _round_price(value: Decimal) -> Decimal:
    """Round a price to two decimal places."""
    return value.quantize(PRICE_PRECISION, rounding=ROUND_HALF_UP)


def _round_minutes(value: Decimal) -> Decimal:
    """Round minutes to one decimal place."""
    return value.quantize(MINUTE_PRECISION, rounding=ROUND_HALF_UP)


def _current_total_price(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Decimal:
    """Return current gross energy price."""
    _ = hass, entry
    return _round_price(data.current_price)


def _current_hour_cost(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Decimal | None:
    """Estimate current cost from an optional power/energy sensor."""
    config = entry.data | entry.options
    entity_id = config.get(CONF_ENERGY_ENTITY)
    if entity_id is None:
        return None

    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable"}:
        return None

    try:
        consumption = Decimal(str(state.state))
    except Exception:  # noqa: BLE001
        return None

    return _round_price(consumption * data.current_price)


def _forecast_min(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Decimal | None:
    """Return minimum forecast price."""
    _ = hass, entry
    value = min((point.price for point in data.forecast), default=None)
    return _round_price(value) if value is not None else None


def _forecast_max(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Decimal | None:
    """Return maximum forecast price."""
    _ = hass, entry
    value = max((point.price for point in data.forecast), default=None)
    return _round_price(value) if value is not None else None


def _current_price_zone(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> str:
    """Return current price zone."""
    _ = hass, entry
    return data.current_price_zone


def _next_price_zone_change(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Any:
    """Return next price zone change timestamp."""
    _ = hass, entry
    return data.next_price_zone_change


def _minutes_to_price_zone_change(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Decimal | None:
    """Return minutes until next price zone change."""
    _ = entry
    if data.next_price_zone_change is None:
        return None
    _ = hass
    seconds = (data.next_price_zone_change - dt_util.utcnow()).total_seconds()
    return _round_minutes(Decimal(str(max(seconds, 0) / 60)))


def _forecast_average(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Decimal | None:
    """Return average forecast price."""
    _ = hass, entry
    if not data.forecast:
        return None
    average = sum((point.price for point in data.forecast), Decimal("0")) / Decimal(
        len(data.forecast)
    )
    return _round_price(average)


SENSORS: tuple[PTESensorEntityDescription, ...] = (
    PTESensorEntityDescription(
        key="current_energy_price",
        translation_key="current_energy_price",
        native_unit_of_measurement=PRICE_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_current_total_price,
        attrs_fn=_base_attrs,
    ),
    PTESensorEntityDescription(
        key="current_hour_cost",
        translation_key="current_hour_cost",
        native_unit_of_measurement=CURRENCY,
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=_current_hour_cost,
        attrs_fn=_base_attrs,
    ),
    PTESensorEntityDescription(
        key="forecast_min_price",
        translation_key="forecast_min_price",
        native_unit_of_measurement=PRICE_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_forecast_min,
        attrs_fn=_forecast_attrs,
    ),
    PTESensorEntityDescription(
        key="forecast_max_price",
        translation_key="forecast_max_price",
        native_unit_of_measurement=PRICE_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_forecast_max,
        attrs_fn=_forecast_attrs,
    ),
    PTESensorEntityDescription(
        key="current_price_zone",
        translation_key="current_price_zone",
        value_fn=_current_price_zone,
        attrs_fn=_base_attrs,
    ),
    PTESensorEntityDescription(
        key="next_price_zone_change",
        translation_key="next_price_zone_change",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_next_price_zone_change,
        attrs_fn=_base_attrs,
    ),
    PTESensorEntityDescription(
        key="minutes_to_price_zone_change",
        translation_key="minutes_to_price_zone_change",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_minutes_to_price_zone_change,
        attrs_fn=_base_attrs,
    ),
    PTESensorEntityDescription(
        key="forecast_average_price",
        translation_key="forecast_average_price",
        native_unit_of_measurement=PRICE_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_forecast_average,
        attrs_fn=_forecast_attrs,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PTE sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        PTESensor(coordinator, entry, description) for description in SENSORS
    )


class PTESensor(CoordinatorEntity[PTEDataUpdateCoordinator], SensorEntity):
    """Representation of a PTE sensor."""

    entity_description: PTESensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PTEDataUpdateCoordinator,
        entry: ConfigEntry,
        description: PTESensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.entity_description = description
        config = entry.data | entry.options
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": config.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": CREATOR,
            "model": config.get(CONF_TARIFF),
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(
            self.coordinator.data,
            self.hass,
            self.entry,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        if self.coordinator.data is None or self.entity_description.attrs_fn is None:
            return {}
        return self.entity_description.attrs_fn(self.coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
