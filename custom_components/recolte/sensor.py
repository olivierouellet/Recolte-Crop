"""Sensors for Récolte: one per followed product, at the entry's location."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Reading
from .const import ATTRIBUTION, DOMAIN, INFO_URL
from .coordinator import RecolteConfigEntry, RecolteCoordinator
from .products import PRODUCTS

DEVICE_CLASSES = {
    "precipitation": SensorDeviceClass.PRECIPITATION,
    "temperature": SensorDeviceClass.TEMPERATURE,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: RecolteConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up one sensor per followed product."""
    coordinator = entry.runtime_data
    async_add_entities(AgClimateSensor(coordinator, key) for key in coordinator.products)


class AgClimateSensor(CoordinatorEntity[RecolteCoordinator], SensorEntity):
    """A product's latest value at the location; the date its period ends is an attribute.

    Récolte Crop Card finds these sensors by their `product` attribute.
    """

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: RecolteCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        product = PRODUCTS[key]
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_icon = product.icon
        self._attr_native_unit_of_measurement = product.unit
        self._attr_suggested_display_precision = product.precision
        self._attr_device_class = DEVICE_CLASSES.get(product.device_class or "")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Agriculture et Agroalimentaire Canada",
            model="AgClimat",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=INFO_URL,
        )

    @property
    def reading(self) -> Reading | None:
        return (self.coordinator.data or {}).get(self._key)

    @property
    def available(self) -> bool:
        return super().available and self.reading is not None

    @property
    def native_value(self) -> float | None:
        reading = self.reading
        return reading.value if reading else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        reading = self.reading
        attrs: dict[str, Any] = {"product": self._key}
        if reading:
            attrs["date"] = reading.date.isoformat()
        return attrs
