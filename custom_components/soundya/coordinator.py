"""DataUpdateCoordinator for Soundya."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SoundyaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Soundya data from Station 2."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{host}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.session = async_get_clientsession(hass)
        self.catalog: list[dict[str, Any]] = []

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch status and glow state from speaker."""
        try:
            async with asyncio.timeout(5):
                # 1. Fetch player status
                async with self.session.get(f"{self.base_url}/api/status") as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"Status error: HTTP {resp.status}")
                    status = await resp.json(content_type=None)

                # 2. Fetch glow state
                glow = {}
                try:
                    async with self.session.get(f"{self.base_url}/api/glow/state") as resp:
                        if resp.status == 200:
                            glow = await resp.json(content_type=None)
                except Exception as err:
                    _LOGGER.debug("Could not fetch glow state: %s", err)

                # 3. Fetch presets
                presets = []
                try:
                    async with self.session.get(f"{self.base_url}/api/glow/presets") as resp:
                        if resp.status == 200:
                            presets = await resp.json(content_type=None)
                except Exception as err:
                    _LOGGER.debug("Could not fetch presets: %s", err)

                # 4. Fetch catalog if not loaded yet
                if not self.catalog:
                    try:
                        async with self.session.get(f"{self.base_url}/api/glow/catalog") as resp:
                            if resp.status == 200:
                                cat_data = await resp.json(content_type=None)
                                self.catalog = cat_data.get("effects", [])
                    except Exception as err:
                        _LOGGER.debug("Could not fetch catalog: %s", err)

                return {
                    "status": status,
                    "glow": glow,
                    "presets": presets,
                    "catalog": self.catalog,
                }
        except TimeoutError as err:
            raise UpdateFailed(f"Timeout communicating with Soundya at {self.host}:{self.port}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Soundya: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_control_cmd(self, cmd: str) -> bool:
        """Send a player command via POST /api/cmd."""
        try:
            async with asyncio.timeout(5):
                async with self.session.post(
                    f"{self.base_url}/api/cmd",
                    data=cmd.encode("utf-8"),
                    headers={"Content-Type": "text/plain; charset=utf-8"},
                ) as resp:
                    await self.async_request_refresh()
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Failed to send command '%s' to Soundya: %s", cmd, err)
            return False

    async def async_set_glow(self, patch: dict[str, Any]) -> bool:
        """Update glow state via POST /api/glow/state."""
        try:
            async with asyncio.timeout(5):
                async with self.session.post(
                    f"{self.base_url}/api/glow/state",
                    json=patch,
                ) as resp:
                    await self.async_request_refresh()
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Failed to update glow state: %s", err)
            return False

    async def async_apply_preset(self, preset_id: str) -> bool:
        """Apply a glow preset via POST /api/glow/presets/apply."""
        try:
            async with asyncio.timeout(5):
                async with self.session.post(
                    f"{self.base_url}/api/glow/presets/apply",
                    json={"id": preset_id},
                ) as resp:
                    await self.async_request_refresh()
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Failed to apply preset '%s': %s", preset_id, err)
            return False

    async def async_set_settings(self, patch: dict[str, Any]) -> bool:
        """Update Soundya settings via POST /api/settings."""
        try:
            async with asyncio.timeout(5):
                async with self.session.post(
                    f"{self.base_url}/api/settings",
                    json=patch,
                ) as resp:
                    await self.async_request_refresh()
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Failed to update settings: %s", err)
            return False
