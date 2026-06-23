"""Constants for Polskie Taryfy Energetyczne."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "polskie_taryfy_energetyczne"
DEFAULT_NAME = "Polskie Taryfy Energetyczne"
CREATOR = "Marcel Kantor"

CONF_TARIFF = "tariff"
CONF_ENERGY_ENTITY = "energy_entity"
CONF_PRICE_SOURCE = "price_source"
CONF_PRESET_OPERATOR = "preset_operator"
CONF_ACTIVE_ENERGY_PRICE_ENTITY = "active_energy_price_entity"
CONF_HIGH_RATE = "high_rate"
CONF_MEDIUM_RATE = "medium_rate"
CONF_LOW_RATE = "low_rate"
CONF_G14_S1_RATE = "g14_s1_rate"
CONF_G14_S2_RATE = "g14_s2_rate"
CONF_G14_S3_RATE = "g14_s3_rate"
CONF_G14_S4_RATE = "g14_s4_rate"

TARIFF_G11 = "G11"
TARIFF_G12 = "G12"
TARIFF_G12W = "G12w"
TARIFF_G13 = "G13"
TARIFF_G14DYNAMIC = "G14dynamic"
TARIFFS = [TARIFF_G11, TARIFF_G12, TARIFF_G12W, TARIFF_G13, TARIFF_G14DYNAMIC]

PRICE_SOURCE_PRESET = "preset"
PRICE_SOURCE_CUSTOM = "custom"

PRICE_ZONE_SINGLE = "single"
PRICE_ZONE_LOW = "low"
PRICE_ZONE_MEDIUM = "medium"
PRICE_ZONE_HIGH = "high"
PRICE_ZONE_G14_S1 = "s1"
PRICE_ZONE_G14_S2 = "s2"
PRICE_ZONE_G14_S3 = "s3"
PRICE_ZONE_G14_S4 = "s4"

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
ATTR_ACTIVE_ENERGY_PRICE = "active_energy_price"
ATTR_ACTIVE_ENERGY_PRICE_ENTITY = "active_energy_price_entity"
ATTR_DISTRIBUTION_PRICE = "distribution_price"
ATTR_PURCHASE_PRICE_AVAILABLE = "purchase_price_available"
