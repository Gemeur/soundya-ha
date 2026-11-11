"""Switch entities for Soundya night mode and settings."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up the Soundya switch entities."""
    coordinator: SoundyaCoordinator = getattr(entry, "runtime_data", None) or hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SoundyaNightModeSwitch(coordinator, entry),
            SoundyaYieldSwitch(coordinator, entry),
            SoundyaEqualizerSwitch(coordinator, entry),
            SoundyaShareHeardSwitch(coordinator, entry),
            SoundyaBypassSwitch(coordinator, entry),
        ]
    )


class SoundyaNightModeSwitch(CoordinatorEntity[SoundyaCoordinator], SwitchEntity):
    """Switch for night mode (Lumya)."""

    _attr_has_entity_name = True
    _attr_name = "Ночной режим"
    _attr_icon = "mdi:weather-night"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_night"

    @property
    def device_info(self) -> DeviceInfo:
        """Return dynamic device info."""
        return self.coordinator.get_device_info(self._entry.entry_id)

    @property
    def available(self) -> bool:
        """Available only when Lumya is active."""
        return super().available and bool(self.coordinator.data.get("lumya_available", False))

    @property
    def is_on(self) -> bool:
        """Return true if night mode is enabled."""
        glow = self.coordinator.data.get("glow", {}) if self.coordinator.data else {}
        return bool(glow.get("night", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.coordinator.async_set_glow({"night": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.coordinator.async_set_glow({"night": False})


class SoundyaYieldSwitch(CoordinatorEntity[SoundyaCoordinator], SwitchEntity):
    """Switch for yielding LED matrix to Alice original animations."""

    _attr_has_entity_name = True
    _attr_name = "Уступать Алисе"
    _attr_icon = "mdi:account-voice"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_yield"

    @property
    def device_info(self) -> DeviceInfo:
        """Return dynamic device info."""
        return self.coordinator.get_device_info(self._entry.entry_id)

    @property
    def available(self) -> bool:
        """Available only when Lumya is active."""
        return super().available and bool(self.coordinator.data.get("lumya_available", False))

    @property
    def is_on(self) -> bool:
        """Return true if yield is enabled."""
        glow = self.coordinator.data.get("glow", {}) if self.coordinator.data else {}
        return bool(glow.get("yield", True))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn yield on."""
        await self.coordinator.async_set_glow({"yield": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn yield off."""
        await self.coordinator.async_set_glow({"yield": False})


class SoundyaEqualizerSwitch(CoordinatorEntity[SoundyaCoordinator], SwitchEntity):
    """Switch for Soundya sound equalizer."""

    _attr_has_entity_name = True
    _attr_name = "Эквалайзер"
    _attr_icon = "mdi:equalizer"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_eq_on"

    @property
    def device_info(self) -> DeviceInfo:
        """Return dynamic device info."""
        return self.coordinator.get_device_info(self._entry.entry_id)

    @property
    def is_on(self) -> bool:
        """Return true if equalizer is enabled."""
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        settings = status.get("settings", {})
        if isinstance(settings, dict):
            return bool(settings.get("eq_on", False))
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn equalizer on."""
        await self.coordinator.async_set_settings({"eq_on": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn equalizer off."""
        await self.coordinator.async_set_settings({"eq_on": False})


class SoundyaShareHeardSwitch(CoordinatorEntity[SoundyaCoordinator], SwitchEntity):
    """Switch for sharing Alice heard phrases via API."""

    _attr_has_entity_name = True
    _attr_name = "Трансляция фраз Алисы"
    _attr_icon = "mdi:ear-hearing"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_share_heard"

    @property
    def device_info(self) -> DeviceInfo:
        """Return dynamic device info."""
        return self.coordinator.get_device_info(self._entry.entry_id)

    @property
    def is_on(self) -> bool:
        """Return true if share heard is enabled."""
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        settings = status.get("settings", {})
        if isinstance(settings, dict):
            return bool(settings.get("share_heard", False))
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn share heard on."""
        await self.coordinator.async_set_settings({"share_heard": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn share heard off."""
        await self.coordinator.async_set_settings({"share_heard": False})


class SoundyaBypassSwitch(CoordinatorEntity[SoundyaCoordinator], SwitchEntity):
    """Switch for Zapret DPI bypass."""

    _attr_has_entity_name = True
    _attr_name = "Обход блокировок (zapret)"
    _attr_icon = "mdi:shield-check"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_bypass_on"

    @property
    def device_info(self) -> DeviceInfo:
        """Return dynamic device info."""
        return self.coordinator.get_device_info(self._entry.entry_id)

    @property
    def is_on(self) -> bool:
        """Return true if bypass is enabled."""
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        settings = status.get("settings", {})
        if isinstance(settings, dict):
            return bool(settings.get("bypass_on", False))
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn bypass on."""
        await self.coordinator.async_set_settings({"bypass_on": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn bypass off."""
        await self.coordinator.async_set_settings({"bypass_on": False})
