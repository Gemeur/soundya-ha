"""Number entities for Soundya."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SoundyaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Soundya number entities."""
    coordinator: SoundyaCoordinator = getattr(entry, "runtime_data", None) or hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SoundyaNightBrightnessNumber(coordinator, entry),
            SoundyaSpeedNumber(coordinator, entry),
            SoundyaIntensityNumber(coordinator, entry),
        ]
    )


class SoundyaNightBrightnessNumber(CoordinatorEntity[SoundyaCoordinator], NumberEntity):
    """Number slider for night mode max brightness."""

    _attr_has_entity_name = True
    _attr_name = "Макс. яркость ночью"
    _attr_icon = "mdi:brightness-4"
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_night_brightness"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Станция 2",
            manufacturer="Яндекс / Soundya",
            model="Яндекс Станция 2",
            configuration_url=coordinator.base_url,
        )

    @property
    def native_value(self) -> float:
        """Return the current night brightness in percent."""
        glow = self.coordinator.data.get("glow", {}) if self.coordinator.data else {}
        val = glow.get("nightBrightness", 0.2)
        return float(round(float(val) * 100.0))

    async def async_set_native_value(self, value: float) -> None:
        """Set night brightness."""
        norm = max(0.0, min(1.0, value / 100.0))
        await self.coordinator.async_set_glow({"nightBrightness": round(norm, 2)})


class SoundyaSpeedNumber(CoordinatorEntity[SoundyaCoordinator], NumberEntity):
    """Number slider for effect speed."""

    _attr_has_entity_name = True
    _attr_name = "Скорость эффектов"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = 10.0
    _attr_native_max_value = 100.0
    _attr_native_step = 5.0
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_speed"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Станция 2",
            manufacturer="Яндекс / Soundya",
            model="Яндекс Станция 2",
            configuration_url=coordinator.base_url,
        )

    @property
    def native_value(self) -> float:
        """Current speed in percent."""
        glow = self.coordinator.data.get("glow", {}) if self.coordinator.data else {}
        val = glow.get("speed", 0.5)
        return float(round(float(val) * 100.0))

    async def async_set_native_value(self, value: float) -> None:
        """Set effect speed."""
        norm = max(0.1, min(1.0, value / 100.0))
        await self.coordinator.async_set_glow({"speed": round(norm, 2)})


class SoundyaIntensityNumber(CoordinatorEntity[SoundyaCoordinator], NumberEntity):
    """Number slider for effect intensity."""

    _attr_has_entity_name = True
    _attr_name = "Интенсивность эффектов"
    _attr_icon = "mdi:tune"
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 5.0
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_intensity"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Станция 2",
            manufacturer="Яндекс / Soundya",
            model="Яндекс Станция 2",
            configuration_url=coordinator.base_url,
        )

    @property
    def native_value(self) -> float:
        """Current intensity in percent."""
        glow = self.coordinator.data.get("glow", {}) if self.coordinator.data else {}
        val = glow.get("intensity", 0.3)
        return float(round(float(val) * 100.0))

    async def async_set_native_value(self, value: float) -> None:
        """Set intensity."""
        norm = max(0.0, min(1.0, value / 100.0))
        await self.coordinator.async_set_glow({"intensity": round(norm, 2)})
