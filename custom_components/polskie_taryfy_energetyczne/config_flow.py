"""Config flow for Polskie Taryfy Energetyczne."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import (
    CONF_DISTRIBUTION_RATE,
    CONF_ENERGY_ENTITY,
    CONF_FIXED_MONTHLY_FEE,
    CONF_NIGHT_RATE,
    CONF_OPERATOR,
    CONF_TARIFF,
    CONF_TAX_RATE,
    CONF_USE_CUSTOM_RATES,
    CONF_ZONE_1_RATE,
    DEFAULT_NAME,
    DOMAIN,
    OPERATORS,
    TARIFFS,
)


class PTEConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Polskie Taryfy Energetyczne."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_OPERATOR]}_{user_input[CONF_TARIFF]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._user_schema(),
            errors=errors,
        )

    def _user_schema(self) -> vol.Schema:
        """Return the user step schema."""
        return vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_OPERATOR): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=value, label=label)
                            for value, label in OPERATORS.items()
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_TARIFF): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=value, label=value)
                            for value in TARIFFS
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_ENERGY_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_USE_CUSTOM_RATES, default=True): bool,
                vol.Required(CONF_ZONE_1_RATE, default=0.75): vol.Coerce(float),
                vol.Optional(CONF_NIGHT_RATE, default=0.42): vol.Coerce(float),
                vol.Optional(CONF_DISTRIBUTION_RATE, default=0.35): vol.Coerce(float),
                vol.Optional(CONF_FIXED_MONTHLY_FEE, default=18.50): vol.Coerce(float),
                vol.Optional(CONF_TAX_RATE, default=23.0): vol.Coerce(float),
            }
        )

