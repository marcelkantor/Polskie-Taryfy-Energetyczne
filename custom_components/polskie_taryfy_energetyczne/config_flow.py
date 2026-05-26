"""Config flow for Polskie Taryfy Energetyczne."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ENERGY_ENTITY,
    CONF_HIGH_RATE,
    CONF_LOW_RATE,
    CONF_PRESET_OPERATOR,
    CONF_PRICE_SOURCE,
    CONF_TARIFF,
    DEFAULT_NAME,
    DOMAIN,
    OPERATORS,
    PRICE_SOURCE_CUSTOM,
    PRICE_SOURCE_PRESET,
    TARIFFS,
)


class PTEConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Polskie Taryfy Energetyczne."""

    VERSION = 1
    _config_data: dict[str, Any]

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return PTEOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._config_data = user_input
            if user_input[CONF_PRICE_SOURCE] == PRICE_SOURCE_CUSTOM:
                return await self.async_step_custom_rates()

            await self.async_set_unique_id(
                f"{user_input[CONF_PRICE_SOURCE]}_{user_input[CONF_TARIFF]}_"
                f"{user_input.get(CONF_PRESET_OPERATOR, 'average')}"
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
        return _base_schema()

    async def async_step_custom_rates(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle custom gross price rates."""
        if user_input is not None:
            data = self._config_data | user_input
            await self.async_set_unique_id(
                f"{data[CONF_PRICE_SOURCE]}_{data[CONF_TARIFF]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=data.get(CONF_NAME, DEFAULT_NAME),
                data=data,
            )

        return self.async_show_form(
            step_id="custom_rates",
            data_schema=_custom_rates_schema(self._config_data),
        )


class PTEOptionsFlow(OptionsFlow):
    """Handle options for Polskie Taryfy Energetyczne."""

    _options_data: dict[str, Any]

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage integration options."""
        if user_input is not None:
            self._options_data = user_input
            if user_input[CONF_PRICE_SOURCE] == PRICE_SOURCE_CUSTOM:
                return await self.async_step_custom_rates()
            return self.async_create_entry(title="", data=user_input)

        values = self.config_entry.data | self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=_base_schema(values),
        )

    async def async_step_custom_rates(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage custom gross price rates."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=self._options_data | user_input,
            )

        values = self.config_entry.data | self.config_entry.options | self._options_data
        return self.async_show_form(
            step_id="custom_rates",
            data_schema=_custom_rates_schema(values),
        )


def _base_schema(values: dict[str, Any] | None = None) -> vol.Schema:
    """Return the base tariff configuration schema."""
    values = values or {}
    return vol.Schema(
        {
            vol.Optional(
                CONF_NAME,
                default=values.get(CONF_NAME, DEFAULT_NAME),
            ): str,
            vol.Required(
                CONF_PRICE_SOURCE,
                default=values.get(CONF_PRICE_SOURCE, PRICE_SOURCE_PRESET),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(
                            value=PRICE_SOURCE_PRESET,
                            label="Preset cena-pradu.pl",
                        ),
                        selector.SelectOptionDict(
                            value=PRICE_SOURCE_CUSTOM,
                            label="Własne ceny brutto",
                        ),
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_PRESET_OPERATOR,
                default=values.get(CONF_PRESET_OPERATOR, next(iter(OPERATORS))),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=value, label=label)
                        for value, label in OPERATORS.items()
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_TARIFF,
                default=values.get(CONF_TARIFF, TARIFFS[0]),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=value, label=value)
                        for value in TARIFFS
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_ENERGY_ENTITY,
                default=values.get(CONF_ENERGY_ENTITY),
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
        }
    )


def _custom_rates_schema(values: dict[str, Any] | None = None) -> vol.Schema:
    """Return the custom gross rates schema."""
    values = values or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_HIGH_RATE,
                default=values.get(CONF_HIGH_RATE, 1.19),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_LOW_RATE,
                default=values.get(CONF_LOW_RATE, 0.64),
            ): vol.Coerce(float),
        }
    )
