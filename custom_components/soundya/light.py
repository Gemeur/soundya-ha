"""Light entity for Soundya backlight / matrix."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SoundyaCoordinator

_LOGGER = logging.getLogger(__name__)

# Native Soundya Ambilight modes (mode_id -> Russian title)
AMBILIGHT_MODES: list[tuple[str, str]] = [
    ("solid", "Ровный"),
    ("pulse", "Пульс"),
    ("eq", "Эквалайзер"),
    ("wave", "Волна"),
    ("rainbow", "Радуга"),
    ("breathe", "Дыхание"),
    ("running", "Бегущий огонь"),
]
AMBILIGHT_ID_TO_NAME: dict[str, str] = dict(AMBILIGHT_MODES)
AMBILIGHT_NAME_TO_ID: dict[str, str] = {v: k for k, v in AMBILIGHT_MODES}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Soundya light entity."""
    coordinator: SoundyaCoordinator = getattr(entry, "runtime_data", None) or hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SoundyaLight(coordinator, entry)])


class SoundyaLight(CoordinatorEntity[SoundyaCoordinator], LightEntity):
    """Adaptive light entity: automatically switches between Lumya and Ambilight."""

    _attr_has_entity_name = True
    _attr_name = "Подсветка"
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_light"

    @property
    def device_info(self) -> DeviceInfo:
        """Return dynamic device info."""
        return self.coordinator.get_device_info(self._entry.entry_id)

    @property
    def is_lumya(self) -> bool:
        """Return True if Lumya mod is active and available."""
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("lumya_available", False))

    @property
    def glow_data(self) -> dict[str, Any]:
        """Return raw glow data from Lumya."""
        return self.coordinator.data.get("glow", {}) if self.coordinator.data else {}

    @property
    def settings_data(self) -> dict[str, Any]:
        """Return raw settings data from Soundya."""
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return status.get("settings", {})

    @property
    def is_on(self) -> bool:
        """Return True if light is on."""
        if self.is_lumya:
            return bool(self.glow_data.get("power", True))
        return bool(self.settings_data.get("ring", False))

    @property
    def brightness(self) -> int:
        """Return the brightness between 0..255."""
        if self.is_lumya:
            b = self.glow_data.get("brightness", 1.0)
            return int(round(float(b) * 255.0))
        b = self.settings_data.get("light_bright", 100)
        return int(round(float(b) * 2.55))

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the RGB color value."""
        if self.is_lumya:
            hex_color = self.glow_data.get("color", "#ff7a00")
        else:
            hex_color = self.settings_data.get("light_color", "#ff7a00")

        hex_clean = str(hex_color).lstrip("#")
        if len(hex_clean) == 6:
            try:
                return (
                    int(hex_clean[0:2], 16),
                    int(hex_clean[2:4], 16),
                    int(hex_clean[4:6], 16),
                )
            except ValueError:
                pass
        return (255, 122, 0)

    @property
    def effect_list(self) -> list[str]:
        """Dynamically return effect list depending on whether Lumya is present."""
        if self.is_lumya:
            catalog = self.coordinator.data.get("catalog", []) if self.coordinator.data else []
            return [e.get("name", e.get("id")) for e in catalog if "name" in e or "id" in e]
        return [name for _, name in AMBILIGHT_MODES]

    @property
    def effect(self) -> str | None:
        """Return the current active effect."""
        if self.is_lumya:
            current_id = self.glow_data.get("effect")
            if not current_id:
                return None
            catalog = self.coordinator.data.get("catalog", []) if self.coordinator.data else []
            for e in catalog:
                if e.get("id") == current_id:
                    return e.get("name", current_id)
            return current_id

        current_mode = self.settings_data.get("light_mode", "solid")
        return AMBILIGHT_ID_TO_NAME.get(current_mode, current_mode)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on or update effect/color/brightness."""
        if self.is_lumya:
            patch: dict[str, Any] = {"power": True}

            if ATTR_BRIGHTNESS in kwargs:
                patch["brightness"] = round(kwargs[ATTR_BRIGHTNESS] / 255.0, 2)

            if ATTR_RGB_COLOR in kwargs:
                r, g, b = kwargs[ATTR_RGB_COLOR]
                patch["color"] = f"#{r:02x}{g:02x}{b:02x}"

            if ATTR_EFFECT in kwargs:
                target_name = kwargs[ATTR_EFFECT]
                catalog = self.coordinator.data.get("catalog", []) if self.coordinator.data else []
                effect_id = target_name
                for e in catalog:
                    if e.get("name") == target_name or e.get("id") == target_name:
                        effect_id = e.get("id")
                        break
                patch["effect"] = effect_id

            await self.coordinator.async_set_glow(patch)
        else:
            patch: dict[str, Any] = {"ring": True}

            if ATTR_BRIGHTNESS in kwargs:
                patch["light_bright"] = max(10, min(100, int(round(kwargs[ATTR_BRIGHTNESS] / 2.55))))

            if ATTR_RGB_COLOR in kwargs:
                r, g, b = kwargs[ATTR_RGB_COLOR]
                patch["light_color"] = f"#{r:02x}{g:02x}{b:02x}"

            if ATTR_EFFECT in kwargs:
                target_name = kwargs[ATTR_EFFECT]
                mode_id = AMBILIGHT_NAME_TO_ID.get(target_name, target_name.lower())
                if mode_id in AMBILIGHT_ID_TO_NAME:
                    patch["light_mode"] = mode_id

            await self.coordinator.async_set_settings(patch)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        if self.is_lumya:
            await self.coordinator.async_set_glow({"power": False})
        else:
            await self.coordinator.async_set_settings({"ring": False})
