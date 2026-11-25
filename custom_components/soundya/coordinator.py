"""DataUpdateCoordinator for Soundya."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SoundyaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Soundya data from speaker."""

    def __init__(self, hass: HomeAssistant, host: str, port: int, pin: str = "") -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{host}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.host = host
        self.port = port
        self.pin = pin.strip()
        self.session_token: str | None = None
        self.base_url = f"http://{host}:{port}"
        self.session = async_get_clientsession(hass)
        self.catalog: list[dict[str, Any]] = []
        self.palettes: list[dict[str, Any]] = []

    def get_device_info(self, entry_id: str) -> DeviceInfo:
        """Return dynamic device info based on current speaker model."""
        status = self.data.get("status", {}) if self.data else {}
        dev = status.get("device", {})
        model = dev.get("model", "Яндекс Станция")
        version = dev.get("version", "0.5.7")
        return DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=model,
            manufacturer="Яндекс / Soundya",
            model=model,
            sw_version=version,
            configuration_url=self.base_url,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch status, mods and glow state from speaker."""
        try:
            async with asyncio.timeout(5):
                # 1. Fetch player status & settings
                async with self.session.get(f"{self.base_url}/api/status") as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"Status error: HTTP {resp.status}")
                    status = await resp.json(content_type=None)

                # 2. Check installed & active mods
                mods_data: dict[str, Any] = {}
                lumya_active = False
                try:
                    async with self.session.get(f"{self.base_url}/api/mods") as resp:
                        if resp.status == 200:
                            mods_data = await resp.json(content_type=None)
                            lumya_active = bool(mods_data.get("active", {}).get("lumya", False))
                except Exception as err:
                    _LOGGER.debug("Could not fetch mods: %s", err)

                # 3. If Lumya is active, fetch glow state, presets & catalog
                glow: dict[str, Any] = {}
                presets: list[dict[str, Any]] = []
                lumya_available = False

                if lumya_active:
                    try:
                        async with self.session.get(f"{self.base_url}/api/glow/state") as resp:
                            if resp.status == 200:
                                glow = await resp.json(content_type=None)
                                lumya_available = True
                    except Exception as err:
                        _LOGGER.debug("Could not fetch glow state: %s", err)

                    if lumya_available:
                        # Fetch presets
                        try:
                            async with self.session.get(f"{self.base_url}/api/glow/presets") as resp:
                                if resp.status == 200:
                                    presets = await resp.json(content_type=None)
                        except Exception as err:
                            _LOGGER.debug("Could not fetch presets: %s", err)

                        # Fetch catalog if not loaded yet
                        if not self.catalog or not self.palettes:
                            try:
                                async with self.session.get(f"{self.base_url}/api/glow/catalog") as resp:
                                    if resp.status == 200:
                                        cat_data = await resp.json(content_type=None)
                                        self.catalog = cat_data.get("effects", [])
                                        self.palettes = cat_data.get("palettes", [])
                            except Exception as err:
                                _LOGGER.debug("Could not fetch catalog: %s", err)

                return {
                    "status": status,
                    "mods": mods_data,
                    "lumya_available": lumya_available,
                    "glow": glow,
                    "presets": presets,
                    "catalog": self.catalog,
                    "palettes": self.palettes,
                }
        except TimeoutError as err:
            raise UpdateFailed(f"Timeout communicating with Soundya at {self.host}:{self.port}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Soundya: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_ensure_login(self) -> bool:
        """Log in to Soundya web panel if PIN is configured."""
        if not self.pin:
            return True
        try:
            async with asyncio.timeout(5):
                async with self.session.post(
                    f"{self.base_url}/api/login",
                    data=self.pin.encode("utf-8"),
                    headers={"Content-Type": "text/plain; charset=utf-8"},
                ) as resp:
                    if resp.status == 200:
                        cookie = resp.cookies.get("soundya_s")
                        if cookie:
                            self.session_token = cookie.value
                            _LOGGER.debug("Successfully authenticated with Soundya panel using PIN")
                            return True
                    text = await resp.text()
                    _LOGGER.warning("Soundya authentication failed: %s (status %s)", text, resp.status)
                    return False
        except Exception as err:
            _LOGGER.warning("Could not log in to Soundya with PIN: %s", err)
            return False

    async def _async_post(
        self,
        endpoint: str,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
    ) -> bool:
        """Send a POST request with automatic PIN authentication."""
        req_headers = dict(headers or {})
        if self.session_token:
            req_headers["Cookie"] = f"soundya_s={self.session_token}"

        url = f"{self.base_url}{endpoint}"
        try:
            async with asyncio.timeout(5):
                async with self.session.post(url, data=data, json=json, headers=req_headers) as resp:
                    if resp.status == 401 and self.pin:
                        _LOGGER.debug("Received 401 from %s, attempting to log in with PIN...", endpoint)
                        if await self.async_ensure_login():
                            retry_headers = dict(headers or {})
                            if self.session_token:
                                retry_headers["Cookie"] = f"soundya_s={self.session_token}"
                            async with self.session.post(url, data=data, json=json, headers=retry_headers) as retry_resp:
                                await self.async_request_refresh()
                                return retry_resp.status == 200
                    await self.async_request_refresh()
                    return resp.status == 200
        except Exception as err:
            _LOGGER.error("Failed POST request to %s: %s", endpoint, err)
            return False

    async def async_control_cmd(self, cmd: str) -> bool:
        """Send a player command via POST /api/cmd."""
        return await self._async_post(
            "/api/cmd",
            data=cmd.encode("utf-8"),
            headers={"Content-Type": "text/plain; charset=utf-8"},
        )

    async def async_alice_say(self, text: str) -> bool:
        """Make Alice speak a phrase out loud."""
        return await self.async_control_cmd(f"alice say {text}")

    async def async_alice_cmd(self, cmd: str) -> bool:
        """Send a control command to Alice."""
        return await self.async_control_cmd(f"alice {cmd}")

    async def async_set_glow(self, patch: dict[str, Any]) -> bool:
        """Update glow state via POST /api/glow/state."""
        return await self._async_post("/api/glow/state", json=patch)

    async def async_apply_preset(self, preset_id: str) -> bool:
        """Apply a glow preset via POST /api/glow/presets/apply."""
        return await self._async_post("/api/glow/presets/apply", json={"id": preset_id})

    async def async_set_settings(self, patch: dict[str, Any]) -> bool:
        """Update Soundya settings via POST /api/settings."""
        return await self._async_post("/api/settings", json=patch)
