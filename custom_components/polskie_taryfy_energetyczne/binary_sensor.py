"""Binary sensors for Polskie Taryfy Energetyczne."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import PTETariffData
from .const import (
    ATTR_FETCHED_AT,
    ATTR_OPERATOR,
    ATTR_PRICE_ZONE,
    ATTR_PRICE_SOURCE,
    ATTR_PRICE_TYPE,
    ATTR_PRESET_YEAR,
    ATTR_SOURCE,
    ATTR_SOURCE_URL,
    ATTR_TARIFF,
    CONF_TARIFF,
    DEFAULT_NAME,
    DOMAIN,
    PRICE_ZONE_LOW,
)
from .coordinator import PTEDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class PTEBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes PTE binary sensor entity."""

    value_fn: Callable[[PTETariffData], bool]
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
    }


def _is_low_price_zone(data: PTETariffData) -> bool:
    """Return true when the current tariff is in a low price zone."""
    return data.current_price_zone == PRICE_ZONE_LOW


def _is_price_below_forecast_average(data: PTETariffData) -> bool:
    """Return true when the current price is not higher than forecast average."""
    if not data.forecast:
        return False
    average = sum((point.price for point in data.forecast), Decimal("0")) / Decimal(
        len(data.forecast)
    )
    return data.current_price <= average


BINARY_SENSORS: tuple[PTEBinarySensorEntityDescription, ...] = (
    PTEBinarySensorEntityDescription(
        key="low_price_zone",
        translation_key="low_price_zone",
        value_fn=_is_low_price_zone,
        attrs_fn=_base_attrs,
    ),
    PTEBinarySensorEntityDescription(
        key="price_below_forecast_average",
        translation_key="price_below_forecast_average",
        value_fn=_is_price_below_forecast_average,
        attrs_fn=_base_attrs,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PTE binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        PTEBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class PTEBinarySensor(CoordinatorEntity[PTEDataUpdateCoordinator], BinarySensorEntity):
    """Representation of a PTE binary sensor."""

    entity_description: PTEBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PTEDataUpdateCoordinator,
        entry: ConfigEntry,
        description: PTEBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        config = entry.data | entry.options
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": config.get(CONF_NAME, DEFAULT_NAME),
            "manufacturer": "Polskie Taryfy Energetyczne",
            "model": config.get(CONF_TARIFF),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

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
