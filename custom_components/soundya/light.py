"""Light entity for Soundya 88-LED matrix on Station 2."""
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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Soundya light entity."""
    coordinator: SoundyaCoordinator = getattr(entry, "runtime_data", None) or hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SoundyaLight(coordinator, entry)])


class SoundyaLight(CoordinatorEntity[SoundyaCoordinator], LightEntity):
    """Representation of the 88-LED matrix light on Station 2."""

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
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Станция 2",
            manufacturer="Яндекс / Soundya",
            model="Яндекс Станция 2",
            configuration_url=coordinator.base_url,
        )

    @property
    def glow_data(self) -> dict[str, Any]:
        """Return raw glow data."""
        return self.coordinator.data.get("glow", {}) if self.coordinator.data else {}

    @property
    def is_on(self) -> bool:
        """Return True if light is on."""
        return bool(self.glow_data.get("power", True))

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        b = self.glow_data.get("brightness", 1.0)
        return int(round(float(b) * 255.0))

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the rgb color value [0..255, 0..255, 0..255]."""
        hex_color = self.glow_data.get("color", "#ff7a00")
        hex_clean = hex_color.lstrip("#")
        if len(hex_clean) == 6:
            try:
                r = int(hex_clean[0:2], 16)
                g = int(hex_clean[2:4], 16)
                b = int(hex_clean[4:6], 16)
                return (r, g, b)
            except ValueError:
                pass
        return (255, 122, 0)

    @property
    def effect_list(self) -> list[str]:
        """Return the list of supported effects."""
        catalog = self.coordinator.data.get("catalog", []) if self.coordinator.data else []
        return [e.get("name", e.get("id")) for e in catalog if "name" in e or "id" in e]

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        current_id = self.glow_data.get("effect")
        if not current_id:
            return None
        catalog = self.coordinator.data.get("catalog", []) if self.coordinator.data else []
        for e in catalog:
            if e.get("id") == current_id:
                return e.get("name", current_id)
        return current_id

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
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

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.coordinator.async_set_glow({"power": False})
