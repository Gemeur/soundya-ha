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
    """Number slider for night mode max brightness (Lumya)."""

    _attr_has_entity_name = True
    _attr_name = "Макс. яркость ночью"
    _attr_icon = "mdi:brightness-4"
    _attr_native_min_value = 5.0
    _attr_native_max_value = 100.0
    _attr_native_step = 5.0
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_night_brightness"

    @property
    def device_info(self) -> DeviceInfo:
        """Return dynamic device info."""
        return self.coordinator.get_device_info(self._entry.entry_id)

    @property
    def available(self) -> bool:
        """Available only when Lumya is active."""
        return super().available and bool(self.coordinator.data.get("lumya_available", False))

    @property
    def native_value(self) -> float:
        """Return current night brightness in percent."""
        glow = self.coordinator.data.get("glow", {}) if self.coordinator.data else {}
        val = glow.get("nightBrightness", 0.2)
        return float(round(float(val) * 100.0))

    async def async_set_native_value(self, value: float) -> None:
        """Set night brightness."""
        norm = max(0.0, min(1.0, value / 100.0))
        await self.coordinator.async_set_glow({"nightBrightness": round(norm, 2)})


class SoundyaSpeedNumber(CoordinatorEntity[SoundyaCoordinator], NumberEntity):
    """Number slider for effect / animation speed."""

    _attr_has_entity_name = True
    _attr_name = "Скорость подсветки"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = 10.0
    _attr_native_max_value = 300.0
    _attr_native_step = 5.0
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_speed"

    @property
    def device_info(self) -> DeviceInfo:
        """Return dynamic device info."""
        return self.coordinator.get_device_info(self._entry.entry_id)

    @property
    def native_value(self) -> float:
        """Current speed in percent."""
        if not self.coordinator.data:
            return 100.0
        if self.coordinator.data.get("lumya_available", False):
            glow = self.coordinator.data.get("glow", {})
            val = glow.get("speed", 0.5)
            return float(round(float(val) * 100.0))

        settings = self.coordinator.data.get("status", {}).get("settings", {})
        return float(settings.get("light_speed", 100))

    async def async_set_native_value(self, value: float) -> None:
        """Set speed."""
        if self.coordinator.data and self.coordinator.data.get("lumya_available", False):
            norm = max(0.1, min(1.0, value / 100.0))
            await self.coordinator.async_set_glow({"speed": round(norm, 2)})
        else:
            await self.coordinator.async_set_settings({"light_speed": int(round(value))})


class SoundyaIntensityNumber(CoordinatorEntity[SoundyaCoordinator], NumberEntity):
    """Number slider for effect intensity / reaction to music."""

    _attr_has_entity_name = True
    _attr_name = "Реакция на музыку"
    _attr_icon = "mdi:waveform"
    _attr_native_min_value = 10.0
    _attr_native_max_value = 200.0
    _attr_native_step = 5.0
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_intensity"

    @property
    def device_info(self) -> DeviceInfo:
        """Return dynamic device info."""
        return self.coordinator.get_device_info(self._entry.entry_id)

    @property
    def native_value(self) -> float:
        """Current intensity in percent."""
        if not self.coordinator.data:
            return 100.0
        if self.coordinator.data.get("lumya_available", False):
            glow = self.coordinator.data.get("glow", {})
            val = glow.get("intensity", 0.5)
            return float(round(float(val) * 100.0))

        settings = self.coordinator.data.get("status", {}).get("settings", {})
        return float(settings.get("light_intensity", 100))

    async def async_set_native_value(self, value: float) -> None:
        """Set intensity."""
        if self.coordinator.data and self.coordinator.data.get("lumya_available", False):
            norm = max(0.1, min(1.0, value / 100.0))
            await self.coordinator.async_set_glow({"intensity": round(norm, 2)})
        else:
            await self.coordinator.async_set_settings({"light_intensity": int(round(value))})
