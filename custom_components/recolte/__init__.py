"""Récolte: Agriculture and Agri-Food Canada's agroclimate data for a location, in Home Assistant."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .coordinator import RecolteConfigEntry, RecolteCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: RecolteConfigEntry) -> bool:
    """Set up Récolte from a config entry."""
    coordinator = RecolteCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    _remove_unfollowed_products(hass, entry, coordinator.products)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RecolteConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: RecolteConfigEntry) -> None:
    """Reload when the products change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _remove_unfollowed_products(hass: HomeAssistant, entry: RecolteConfigEntry, products: list[str]) -> None:
    """Drop the sensors of products taken out in the options, rather than leave them unavailable."""
    registry = er.async_get(hass)
    kept = {f"{entry.entry_id}_{p}" for p in products}
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.unique_id not in kept:
            registry.async_remove(entity.entity_id)
