"""Button entities for Soundya on Station 2."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
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
    """Set up Soundya button entities."""
    coordinator: SoundyaCoordinator = getattr(entry, "runtime_data", None) or hass.data[DOMAIN][entry.entry_id]

    entities: list[ButtonEntity] = [
        SoundyaLikeButton(coordinator, entry),
        SoundyaDislikeButton(coordinator, entry),
        SoundyaNetCheckButton(coordinator, entry),
    ]

    async_add_entities(entities)


class SoundyaBaseButton(CoordinatorEntity[SoundyaCoordinator], ButtonEntity):
    """Base button for Soundya."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry, key: str, name: str) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Станция 2",
            manufacturer="Яндекс / Soundya",
            model="Яндекс Станция 2",
            configuration_url=coordinator.base_url,
        )


class SoundyaLikeButton(SoundyaBaseButton):
    """Button to like current track in SoundCloud."""

    _attr_icon = "mdi:heart"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry, "like_track", "Лайкнуть текущий трек")

    async def async_press(self) -> None:
        """Handle button press."""
        await self.coordinator.async_control_cmd("like")


class SoundyaDislikeButton(SoundyaBaseButton):
    """Button to unlike current track in SoundCloud."""

    _attr_icon = "mdi:heart-broken"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry, "unlike_track", "Удалить из любимых")

    async def async_press(self) -> None:
        """Handle button press."""
        await self.coordinator.async_control_cmd("unlike")


class SoundyaNetCheckButton(SoundyaBaseButton):
    """Button to run connection probe."""

    _attr_icon = "mdi:network-check"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry, "check_net", "Проверить сеть")

    async def async_press(self) -> None:
        """Handle button press."""
        await self.coordinator.async_control_cmd("probe")
