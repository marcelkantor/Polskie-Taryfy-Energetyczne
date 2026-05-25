"""Sensors for Polskie Taryfy Energetyczne."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import PTETariffData
from .const import (
    ATTR_DISTRIBUTION_RATE,
    ATTR_FETCHED_AT,
    ATTR_FIXED_MONTHLY_FEE,
    ATTR_FORECAST,
    ATTR_OPERATOR,
    ATTR_TARIFF,
    ATTR_TAX_RATE,
    CONF_ENERGY_ENTITY,
    CONF_TARIFF,
    DEFAULT_NAME,
    DOMAIN,
)
from .coordinator import PTEDataUpdateCoordinator

PRICE_UNIT = "PLN/kWh"
CURRENCY = "PLN"


@dataclass(frozen=True, kw_only=True)
class PTESensorEntityDescription(SensorEntityDescription):
    """Describes PTE sensor entity."""

    value_fn: Callable[[PTETariffData, HomeAssistant, ConfigEntry], Decimal | None]
    attrs_fn: Callable[[PTETariffData], dict[str, Any]] | None = None


def _base_attrs(data: PTETariffData) -> dict[str, Any]:
    """Return common state attributes."""
    return {
        ATTR_OPERATOR: data.operator,
        ATTR_TARIFF: data.tariff,
        ATTR_DISTRIBUTION_RATE: float(data.distribution_rate),
        ATTR_FIXED_MONTHLY_FEE: float(data.fixed_monthly_fee),
        ATTR_TAX_RATE: float(data.tax_rate),
        ATTR_FETCHED_AT: data.fetched_at.isoformat(),
    }


def _forecast_attrs(data: PTETariffData) -> dict[str, Any]:
    """Return compact forecast attributes."""
    attrs = _base_attrs(data)
    attrs[ATTR_FORECAST] = [
        {
            "start": point.start.isoformat(),
            "end": point.end.isoformat(),
            "price": float(point.price),
        }
        for point in data.forecast
    ]
    return attrs


def _current_total_price(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Decimal:
    """Return total current price including distribution."""
    _ = hass, entry
    return data.current_price + data.distribution_rate


def _current_hour_cost(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Decimal | None:
    """Estimate current hourly cost from an optional power/energy sensor."""
    entity_id = entry.data.get(CONF_ENERGY_ENTITY)
    if entity_id is None:
        return None

    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable"}:
        return None

    try:
        consumption = Decimal(str(state.state))
    except Exception:  # noqa: BLE001
        return None

    return consumption * (data.current_price + data.distribution_rate)


def _forecast_min(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Decimal | None:
    """Return minimum forecast price."""
    _ = hass, entry
    return min((point.price for point in data.forecast), default=None)


def _forecast_max(
    data: PTETariffData,
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Decimal | None:
    """Return maximum forecast price."""
    _ = hass, entry
    return max((point.price for point in data.forecast), default=None)


SENSORS: tuple[PTESensorEntityDescription, ...] = (
    PTESensorEntityDescription(
        key="current_energy_price",
        translation_key="current_energy_price",
        native_unit_of_measurement=PRICE_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_current_total_price,
        attrs_fn=_base_attrs,
    ),
    PTESensorEntityDescription(
        key="current_hour_cost",
        translation_key="current_hour_cost",
        native_unit_of_measurement=CURRENCY,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_current_hour_cost,
        attrs_fn=_base_attrs,
    ),
    PTESensorEntityDescription(
        key="forecast_min_price",
        translation_key="forecast_min_price",
        native_unit_of_measurement=PRICE_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_forecast_min,
        attrs_fn=_forecast_attrs,
    ),
    PTESensorEntityDescription(
        key="forecast_max_price",
        translation_key="forecast_max_price",
        native_unit_of_measurement=PRICE_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_forecast_max,
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
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "Polskie Taryfy Energetyczne",
            "model": entry.data.get(CONF_TARIFF),
        }

    @property
    def native_value(self) -> Decimal | None:
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
