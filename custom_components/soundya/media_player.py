"""Media Player entity for Soundya on Station 2."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    RepeatMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import SoundyaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Soundya media player entity."""
    coordinator: SoundyaCoordinator = getattr(entry, "runtime_data", None) or hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SoundyaMediaPlayer(coordinator, entry)])


class SoundyaMediaPlayer(CoordinatorEntity[SoundyaCoordinator], MediaPlayerEntity):
    """Representation of the Soundya media player on Station 2."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER

    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.SHUFFLE_SET
        | MediaPlayerEntityFeature.REPEAT_SET
        | MediaPlayerEntityFeature.PLAY_MEDIA
    )
    _attr_source_list = ["soundya", "alice", "airplay", "bluetooth", "idle"]

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_player"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Станция 2",
            manufacturer="Яндекс / Soundya",
            model="Яндекс Станция 2",
            configuration_url=coordinator.base_url,
        )

    @property
    def status_data(self) -> dict[str, Any]:
        """Return raw player status dict."""
        return self.coordinator.data.get("status", {}) if self.coordinator.data else {}

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the player."""
        st = self.status_data.get("state")
        if st == "playing":
            return MediaPlayerState.PLAYING
        if st == "paused":
            return MediaPlayerState.PAUSED
        return MediaPlayerState.IDLE

    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        return self.status_data.get("title")

    @property
    def media_artist(self) -> str | None:
        """Artist of current playing media."""
        return self.status_data.get("artist")

    @property
    def media_image_url(self) -> str | None:
        """Image URL of current playing media."""
        cover = self.status_data.get("cover")
        if not cover:
            return None
        if str(cover).startswith("http://") or str(cover).startswith("https://"):
            return str(cover)
        return f"{self.coordinator.base_url}{cover}"

    @property
    def media_duration(self) -> int | None:
        """Duration of current playing media in seconds."""
        ms = self.status_data.get("duration_ms")
        if ms and ms > 0:
            return int(ms // 1000)
        return None

    @property
    def media_position(self) -> int | None:
        """Position of current playing media in seconds."""
        ms = self.status_data.get("position_ms")
        if ms is not None and ms >= 0:
            return int(ms // 1000)
        return None

    @property
    def media_position_updated_at(self) -> Any:
        """When the position was last updated."""
        if self.state == MediaPlayerState.PLAYING:
            return dt_util.utcnow()
        return None

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1.0)."""
        vol = self.status_data.get("volume")
        if vol is not None:
            return max(0.0, min(1.0, float(vol) / 10.0))
        return None

    @property
    def shuffle(self) -> bool:
        """Boolean if shuffle is enabled."""
        return bool(self.status_data.get("shuffle", False))

    @property
    def repeat(self) -> RepeatMode:
        """Return current repeat mode."""
        return RepeatMode.ONE if self.status_data.get("repeat") else RepeatMode.OFF

    @property
    def source(self) -> str | None:
        """Name of the current input source."""
        return self.status_data.get("source")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return speaker extra attributes."""
        attrs: dict[str, Any] = {}
        if heard := self.status_data.get("heard"):
            if isinstance(heard, dict):
                attrs["last_heard"] = heard.get("text")
                attrs["last_heard_at"] = heard.get("at")
            elif isinstance(heard, str):
                attrs["last_heard"] = heard
        if current_url := self.status_data.get("current_url"):
            attrs["current_url"] = current_url
        if liked := self.status_data.get("current_liked"):
            attrs["liked"] = liked
        return attrs

    async def async_play_media(self, media_type: str, media_id: str, **kwargs: Any) -> None:
        """Play media by title, search query or SoundCloud URL."""
        await self.coordinator.async_control_cmd(f"play {media_id}")

    async def async_media_play(self) -> None:
        """Play media."""
        await self.coordinator.async_control_cmd("resume")

    async def async_media_pause(self) -> None:
        """Pause media."""
        await self.coordinator.async_control_cmd("pause")

    async def async_media_stop(self) -> None:
        """Stop media."""
        await self.coordinator.async_control_cmd("pause")

    async def async_media_next_track(self) -> None:
        """Next track."""
        await self.coordinator.async_control_cmd("next")

    async def async_media_previous_track(self) -> None:
        """Previous track."""
        await self.coordinator.async_control_cmd("prev")

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        level = int(round(volume * 10))
        await self.coordinator.async_control_cmd(f"volume set {level}")

    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Enable/disable shuffle mode."""
        await self.coordinator.async_control_cmd(f"shuffle {'on' if shuffle else 'off'}")

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        """Set repeat mode."""
        is_on = repeat != RepeatMode.OFF
        await self.coordinator.async_control_cmd(f"repeat {'on' if is_on else 'off'}")
