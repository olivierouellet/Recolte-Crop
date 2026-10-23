"""Data coordinator for Récolte."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AgClimateApiError, AgClimateClient, Reading
from .const import CONF_PRODUCTS, DOMAIN, FETCH_INTERVAL
from .products import DEFAULT_PRODUCTS, PRODUCTS

_LOGGER = logging.getLogger(__name__)

type RecolteConfigEntry = ConfigEntry[RecolteCoordinator]


class RecolteCoordinator(DataUpdateCoordinator[dict[str, Reading]]):
    """Reads the followed products at the entry's location every few hours."""

    config_entry: RecolteConfigEntry

    def __init__(self, hass: HomeAssistant, entry: RecolteConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=FETCH_INTERVAL,
        )
        self.client = AgClimateClient(async_get_clientsession(hass))
        self.latitude: float = entry.data[CONF_LATITUDE]
        self.longitude: float = entry.data[CONF_LONGITUDE]
        self.products: list[str] = [p for p in entry.options.get(CONF_PRODUCTS, DEFAULT_PRODUCTS) if p in PRODUCTS]

    async def _async_update_data(self) -> dict[str, Reading]:
        try:
            readings = await self.client.async_readings(self.latitude, self.longitude, self.products)
        except AgClimateApiError as err:
            if self.data is None:
                raise UpdateFailed(str(err)) from err
            # The values change at most daily: keep the last ones rather than turn the sensors unavailable.
            _LOGGER.warning("Could not refresh the agroclimate data, keeping the last values: %s", err)
            return self.data
        # A service that failed alone leaves its products out: keep their last values too.
        previous = {k: v for k, v in (self.data or {}).items() if k in self.products}
        return {**previous, **readings}
