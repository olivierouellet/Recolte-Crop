"""Config and options flows for Récolte: a location (the home, or anywhere on the map) and its products."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_LATITUDE, CONF_LOCATION, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    LocationSelector,
    LocationSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .api import AgClimateApiError, AgClimateClient
from .const import CONF_PRODUCTS, DOMAIN
from .products import DEFAULT_PRODUCTS, PRODUCTS

_LOGGER = logging.getLogger(__name__)


def _products_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=list(PRODUCTS),
            multiple=True,
            mode=SelectSelectorMode.DROPDOWN,
            translation_key="product",
        )
    )


def _products(selected: list[str]) -> list[str]:
    """In catalog order, so sensors and the card list them the same way every time."""
    chosen = set(selected)
    return [p for p in PRODUCTS if p in chosen]


class RecolteConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a location; each location is its own entry and device."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            latitude = round(float(user_input[CONF_LOCATION][CONF_LATITUDE]), 4)
            longitude = round(float(user_input[CONF_LOCATION][CONF_LONGITUDE]), 4)
            await self.async_set_unique_id(f"{latitude:.3f},{longitude:.3f}")
            self._abort_if_unique_id_configured()
            if not user_input[CONF_PRODUCTS]:
                errors[CONF_PRODUCTS] = "no_product"
            else:
                client = AgClimateClient(async_get_clientsession(self.hass))
                try:
                    covered = await client.async_covers(latitude, longitude)
                except AgClimateApiError as err:
                    _LOGGER.warning("Could not reach the AgClimate service: %s", err)
                    errors["base"] = "cannot_connect"
                else:
                    if not covered:
                        errors[CONF_LOCATION] = "outside_coverage"
                    else:
                        return self.async_create_entry(
                            title=user_input[CONF_NAME].strip() or self.hass.config.location_name,
                            data={CONF_LATITUDE: latitude, CONF_LONGITUDE: longitude},
                            options={CONF_PRODUCTS: _products(user_input[CONF_PRODUCTS])},
                        )

        defaults: dict[str, Any] = {
            CONF_NAME: self.hass.config.location_name,
            CONF_LOCATION: {CONF_LATITUDE: self.hass.config.latitude, CONF_LONGITUDE: self.hass.config.longitude},
            CONF_PRODUCTS: DEFAULT_PRODUCTS,
        }
        if user_input is not None:
            defaults = {**defaults, **user_input}
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=defaults[CONF_NAME]): TextSelector(),
                vol.Required(CONF_LOCATION, default=defaults[CONF_LOCATION]): LocationSelector(
                    LocationSelectorConfig(radius=False)
                ),
                vol.Required(CONF_PRODUCTS, default=defaults[CONF_PRODUCTS]): _products_selector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> RecolteOptionsFlow:
        return RecolteOptionsFlow()


class RecolteOptionsFlow(OptionsFlow):
    """Change the products followed at a location."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_PRODUCTS]:
                return self.async_create_entry(data={CONF_PRODUCTS: _products(user_input[CONF_PRODUCTS])})
            errors[CONF_PRODUCTS] = "no_product"

        current = self.config_entry.options.get(CONF_PRODUCTS, DEFAULT_PRODUCTS)
        schema = vol.Schema({vol.Required(CONF_PRODUCTS, default=current): _products_selector()})
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
