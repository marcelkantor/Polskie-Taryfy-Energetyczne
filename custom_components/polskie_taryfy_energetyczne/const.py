"""Constants for Polskie Taryfy Energetyczne."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "polskie_taryfy_energetyczne"
DEFAULT_NAME = "Polskie Taryfy Energetyczne"

CONF_TARIFF = "tariff"
CONF_ENERGY_ENTITY = "energy_entity"
CONF_PRICE_SOURCE = "price_source"
CONF_PRESET_OPERATOR = "preset_operator"
CONF_HIGH_RATE = "high_rate"
CONF_LOW_RATE = "low_rate"

TARIFF_G11 = "G11"
TARIFF_G12 = "G12"
TARIFF_G12W = "G12w"
TARIFFS = [TARIFF_G11, TARIFF_G12, TARIFF_G12W]

PRICE_SOURCE_PRESET = "preset"
PRICE_SOURCE_CUSTOM = "custom"

PRICE_ZONE_SINGLE = "single"
PRICE_ZONE_LOW = "low"
PRICE_ZONE_HIGH = "high"

OPERATORS = {
    "enea": "Enea",
    "energa": "Energa",
    "pge": "PGE",
    "tauron": "Tauron",
    "eon": "E.ON",
}

DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
ATTR_FORECAST = "forecast"
ATTR_TARIFF = "tariff"
ATTR_OPERATOR = "operator"
ATTR_FETCHED_AT = "fetched_at"
ATTR_PRICE_ZONE = "price_zone"
ATTR_PRICE_SOURCE = "price_source"
ATTR_PRICE_TYPE = "price_type"
ATTR_PRESET_YEAR = "preset_year"
ATTR_SOURCE = "source"
ATTR_SOURCE_URL = "source_url"
