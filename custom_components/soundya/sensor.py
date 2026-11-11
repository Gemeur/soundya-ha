"""Sensors for Soundya on Station 2."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
    UnitOfTime,
)
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
    """Set up Soundya sensor entities."""
    coordinator: SoundyaCoordinator = getattr(entry, "runtime_data", None) or hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        SoundyaLastHeardSensor(coordinator, entry),
        SoundyaSourceSensor(coordinator, entry),
        SoundyaWifiSignalSensor(coordinator, entry),
        SoundyaPingSensor(coordinator, entry),
        SoundyaCpuTempSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class SoundyaBaseSensor(CoordinatorEntity[SoundyaCoordinator], SensorEntity):
    """Base class for Soundya sensors."""

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

    @property
    def status_data(self) -> dict[str, Any]:
        """Return raw player status dict."""
        return self.coordinator.data.get("status", {}) if self.coordinator.data else {}


class SoundyaLastHeardSensor(SoundyaBaseSensor):
    """Sensor for the last phrase recognized by Alice."""

    _attr_icon = "mdi:microphone-message"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry, "last_heard", "Последняя фраза Алисы")

    @property
    def native_value(self) -> str | None:
        """Return last heard phrase."""
        heard = self.status_data.get("heard")
        if isinstance(heard, dict):
            return heard.get("text")
        if isinstance(heard, str):
            return heard
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        heard = self.status_data.get("heard")
        if isinstance(heard, dict):
            return {"at": heard.get("at")}
        return {}


class SoundyaSourceSensor(SoundyaBaseSensor):
    """Sensor for active audio source."""

    _attr_icon = "mdi:speaker-wireless"

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry, "source", "Источник звука")

    @property
    def native_value(self) -> str | None:
        """Return active audio source."""
        return self.status_data.get("source")


class SoundyaWifiSignalSensor(SoundyaBaseSensor):
    """Sensor for Wi-Fi RSSI signal strength."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry, "wifi_signal", "Сигнал Wi-Fi")

    @property
    def native_value(self) -> int | None:
        """Return Wi-Fi RSSI."""
        net = self.status_data.get("net", {})
        if isinstance(net, dict):
            return net.get("rssi")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return wifi extra info."""
        net = self.status_data.get("net", {})
        if isinstance(net, dict):
            attrs = {}
            if "wifi_quality" in net:
                attrs["quality_pct"] = net["wifi_quality"]
            if "mac" in net:
                attrs["mac"] = net["mac"]
            if "ip" in net:
                attrs["ip"] = net["ip"]
            return attrs
        return {}


class SoundyaPingSensor(SoundyaBaseSensor):
    """Sensor for network ping."""

    _attr_icon = "mdi:speedometer"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry, "ping", "Пинг сети")

    @property
    def native_value(self) -> int | None:
        """Return ping in ms."""
        net = self.status_data.get("net", {})
        if isinstance(net, dict):
            return net.get("ping_ms")
        return None


class SoundyaCpuTempSensor(SoundyaBaseSensor):
    """Sensor for CPU temperature."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: SoundyaCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator, entry, "cpu_temperature", "Температура процессора")

    @property
    def native_value(self) -> float | None:
        """Return CPU temperature in C."""
        sys = self.status_data.get("sys", {})
        if isinstance(sys, dict) and sys.get("cpu_temp") is not None:
            return round(float(sys["cpu_temp"]), 1)
        return None

    @property
    def available(self) -> bool:
        """Available only when CPU temperature is provided by system info."""
        sys = self.status_data.get("sys", {})
        return isinstance(sys, dict) and sys.get("cpu_temp") is not None
