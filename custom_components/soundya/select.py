"""Select entities for Soundya presets, combined effects, and color palettes."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SoundyaCoordinator

_LOGGER = logging.getLogger(__name__)

SEPARATOR = "─── Эффекты под музыку ───"

BUILTIN_PALETTES = [
    ("aurora", "Северное сияние"),
    ("sunset", "Закат"),
    ("ocean", "Океан"),
    ("ember", "Угли"),
    ("sakura", "Сакура"),
    ("forest", "Лес"),
    ("rainbow", "Радуга"),
    ("ice", "Лёд"),
    ("candy", "Конфета"),
    ("cyber", "Киберпанк"),
    ("party", "Вечеринка"),
    ("matrix", "Матрица"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Soundya select entities."""
    coordinator: SoundyaCoordinator = getattr(entry, "runtime_data", None) or hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SoundyaEffectSelect(coordinator, entry),
            SoundyaPaletteSelect(coordinator, entry),
            SoundyaPresetSelect(coordinator, entry),
        ]
    )


class SoundyaEffectSelect(CoordinatorEntity[SoundyaCoordinator], SelectEntity):
    """Combined selector for calm and music effects with a separator."""

    _attr_has_entity_name = True
    _attr_name = "Эффект подсветки"
    _attr_icon = "mdi:creation-outline"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_effect"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Станция 2",
            manufacturer="Яндекс / Soundya",
            model="Яндекс Станция 2",
            configuration_url=coordinator.base_url,
        )

    @property
    def options(self) -> list[str]:
        """Return combined effects: calm, separator, music."""
        catalog = self.coordinator.data.get("catalog", []) if self.coordinator.data else []
        calm = [e.get("name", e.get("id")) for e in catalog if not e.get("music")]
        music = [e.get("name", e.get("id")) for e in catalog if e.get("music")]
        return calm + [SEPARATOR] + music

    @property
    def current_option(self) -> str | None:
        """Return current effect name."""
        glow = self.coordinator.data.get("glow", {}) if self.coordinator.data else {}
        cur_id = glow.get("effect")
        catalog = self.coordinator.data.get("catalog", []) if self.coordinator.data else []
        for e in catalog:
            if e.get("id") == cur_id:
                return e.get("name", cur_id)
        return cur_id

    async def async_select_option(self, option: str) -> None:
        """Apply chosen effect, ignoring the separator."""
        if option == SEPARATOR:
            return
        catalog = self.coordinator.data.get("catalog", []) if self.coordinator.data else []
        effect_id = option
        for e in catalog:
            if e.get("name") == option or e.get("id") == option:
                effect_id = e.get("id")
                break
        await self.coordinator.async_set_glow({"effect": effect_id, "power": True})


class SoundyaPaletteSelect(CoordinatorEntity[SoundyaCoordinator], SelectEntity):
    """Selector for color palettes."""

    _attr_has_entity_name = True
    _attr_name = "Цветовая палитра"
    _attr_icon = "mdi:palette"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_palette"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Станция 2",
            manufacturer="Яндекс / Soundya",
            model="Яндекс Станция 2",
            configuration_url=coordinator.base_url,
        )

    @property
    def options(self) -> list[str]:
        """Return list of palette names."""
        return [name for _, name in BUILTIN_PALETTES]

    @property
    def current_option(self) -> str | None:
        """Return current palette name."""
        glow = self.coordinator.data.get("glow", {}) if self.coordinator.data else {}
        cur_pal = glow.get("palette", "aurora")
        for pal_id, name in BUILTIN_PALETTES:
            if pal_id == cur_pal:
                return name
        return cur_pal

    async def async_select_option(self, option: str) -> None:
        """Apply chosen color palette."""
        target_id = option
        for pal_id, name in BUILTIN_PALETTES:
            if name == option or pal_id == option:
                target_id = pal_id
                break
        await self.coordinator.async_set_glow({"palette": target_id})


class SoundyaPresetSelect(CoordinatorEntity[SoundyaCoordinator], SelectEntity):
    """Selector for Glow presets."""

    _attr_has_entity_name = True
    _attr_name = "Пресет подсветки"
    _attr_icon = "mdi:palette-swatch-outline"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_preset"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Станция 2",
            manufacturer="Яндекс / Soundya",
            model="Яндекс Станция 2",
            configuration_url=coordinator.base_url,
        )

    @property
    def options(self) -> list[str]:
        """Return the list of available presets."""
        presets = self.coordinator.data.get("presets", []) if self.coordinator.data else []
        return [p.get("name", p.get("id")) for p in presets if "name" in p or "id" in p]

    @property
    def current_option(self) -> str | None:
        """Return current preset if matching."""
        glow = self.coordinator.data.get("glow", {}) if self.coordinator.data else {}
        presets = self.coordinator.data.get("presets", []) if self.coordinator.data else []
        cur_fx = glow.get("effect")
        for p in presets:
            if p.get("effect") == cur_fx:
                return p.get("name", p.get("id"))
        return self.options[0] if self.options else None

    async def async_select_option(self, option: str) -> None:
        """Apply preset."""
        presets = self.coordinator.data.get("presets", []) if self.coordinator.data else []
        target_id = option
        for p in presets:
            if p.get("name") == option or p.get("id") == option:
                target_id = p.get("id")
                break
        await self.coordinator.async_apply_preset(target_id)
