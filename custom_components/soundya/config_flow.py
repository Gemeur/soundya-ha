"""Config flow for Soundya integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
import voluptuous as vol

from .const import DEFAULT_NAME, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SoundyaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Soundya."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._discovered_host: str | None = None
        self._discovered_port: int = DEFAULT_PORT

    async def _async_validate_connection(self, host: str, port: int) -> dict[str, Any] | None:
        """Validate connection and retrieve initial status."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(f"http://{host}:{port}/api/status", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
        except Exception as err:
            _LOGGER.debug("Connection test failed for %s:%s: %s", host, port, err)
        return None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle manual user configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = int(user_input.get(CONF_PORT, DEFAULT_PORT))

            status = await self._async_validate_connection(host, port)
            if status is not None:
                unique_id = f"soundya_{host.replace('.', '_')}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                title = DEFAULT_NAME
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                    },
                )
            errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=self._discovered_host or ""): str,
                vol.Optional(CONF_PORT, default=self._discovered_port): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> FlowResult:
        """Handle zeroconf discovery."""
        host = discovery_info.host
        port = discovery_info.port or DEFAULT_PORT

        unique_id = f"soundya_{host.replace('.', '_')}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured({CONF_HOST: host, CONF_PORT: port})

        self._discovered_host = host
        self._discovered_port = port

        self.context.update(
            {
                "title_placeholders": {"name": f"{DEFAULT_NAME} ({host})"},
                "configuration_url": f"http://{host}:{port}",
            }
        )

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Confirm zeroconf discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"{DEFAULT_NAME} ({self._discovered_host})",
                data={
                    CONF_HOST: self._discovered_host,
                    CONF_PORT: self._discovered_port,
                },
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "name": DEFAULT_NAME,
                "host": self._discovered_host or "",
            },
        )
