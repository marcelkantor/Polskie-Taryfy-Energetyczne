"""Constants for Polskie Taryfy Energetyczne."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "polskie_taryfy_energetyczne"
DEFAULT_NAME = "Polskie Taryfy Energetyczne"

CONF_OPERATOR = "operator"
CONF_TARIFF = "tariff"
CONF_ENERGY_ENTITY = "energy_entity"
CONF_USE_CUSTOM_RATES = "use_custom_rates"
CONF_HIGH_RATE = "high_rate"
CONF_LOW_RATE = "low_rate"
CONF_DISTRIBUTION_RATE = "distribution_rate"
CONF_FIXED_MONTHLY_FEE = "fixed_monthly_fee"
CONF_TAX_RATE = "tax_rate"

TARIFF_G11 = "G11"
TARIFF_G12 = "G12"
TARIFF_G12W = "G12w"
TARIFFS = [TARIFF_G11, TARIFF_G12, TARIFF_G12W]

PRICE_ZONE_SINGLE = "single"
PRICE_ZONE_LOW = "low"
PRICE_ZONE_HIGH = "high"

OPERATORS = {
    "enea": "Enea",
    "energa": "Energa",
    "pge": "PGE",
    "tauron": "Tauron",
    "eon": "E.ON",
    "other": "Inny operator",
}

DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
ATTR_FORECAST = "forecast"
ATTR_TARIFF = "tariff"
ATTR_OPERATOR = "operator"
ATTR_FETCHED_AT = "fetched_at"
ATTR_PRICE_ZONE = "price_zone"
ATTR_DISTRIBUTION_RATE = "distribution_rate"
ATTR_FIXED_MONTHLY_FEE = "fixed_monthly_fee"
ATTR_TAX_RATE = "tax_rate"
