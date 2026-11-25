"""Config flow for Soundya integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
import voluptuous as vol

from .const import CONF_PIN, DEFAULT_NAME, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SoundyaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Soundya."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._discovered_host: str | None = None
        self._discovered_port: int = DEFAULT_PORT

    async def _async_validate_connection(
        self, host: str, port: int, pin: str = ""
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Validate connection and retrieve initial status."""
        session = async_get_clientsession(self.hass)
        status = None
        try:
            async with session.get(f"http://{host}:{port}/api/status", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    status = await resp.json(content_type=None)
        except Exception as err:
            _LOGGER.debug("Connection test failed for %s:%s: %s", host, port, err)
            return None, "cannot_connect"

        if status is None:
            return None, "cannot_connect"

        pin_on = bool(status.get("settings", {}).get("pin_on", False))
        if pin:
            try:
                async with session.post(
                    f"http://{host}:{port}/api/login",
                    data=pin.encode("utf-8"),
                    headers={"Content-Type": "text/plain; charset=utf-8"},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status != 200:
                        return status, "invalid_auth"
            except Exception as err:
                _LOGGER.debug("PIN verification failed: %s", err)
                return status, "cannot_connect"
        elif pin_on:
            return status, "pin_required"

        return status, None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle manual user configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = int(user_input.get(CONF_PORT, DEFAULT_PORT))
            pin = user_input.get(CONF_PIN, "").strip()

            status, err = await self._async_validate_connection(host, port, pin)
            if err is not None:
                errors["base"] = err
            elif status is not None:
                unique_id = f"soundya_{host.replace('.', '_')}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                title = DEFAULT_NAME
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_PIN: pin,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=self._discovered_host or ""): str,
                vol.Optional(CONF_PORT, default=self._discovered_port): int,
                vol.Optional(CONF_PIN, default=""): str,
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
        errors: dict[str, str] = {}

        if user_input is not None:
            pin = user_input.get(CONF_PIN, "").strip()
            status, err = await self._async_validate_connection(self._discovered_host, self._discovered_port, pin)
            if err is not None:
                errors["base"] = err
            else:
                return self.async_create_entry(
                    title=f"{DEFAULT_NAME} ({self._discovered_host})",
                    data={
                        CONF_HOST: self._discovered_host,
                        CONF_PORT: self._discovered_port,
                        CONF_PIN: pin,
                    },
                )

        schema = vol.Schema(
            {
                vol.Optional(CONF_PIN, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=schema,
            description_placeholders={
                "name": DEFAULT_NAME,
                "host": self._discovered_host or "",
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return SoundyaOptionsFlow(config_entry)


class SoundyaOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Soundya."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage Soundya options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            pin = user_input.get(CONF_PIN, "").strip()
            host = self.config_entry.data[CONF_HOST]
            port = self.config_entry.data.get(CONF_PORT, DEFAULT_PORT)

            if pin:
                session = async_get_clientsession(self.hass)
                try:
                    async with session.post(
                        f"http://{host}:{port}/api/login",
                        data=pin.encode("utf-8"),
                        headers={"Content-Type": "text/plain; charset=utf-8"},
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as resp:
                        if resp.status != 200:
                            errors["base"] = "invalid_auth"
                except Exception:
                    errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        current_pin = self.config_entry.options.get(
            CONF_PIN, self.config_entry.data.get(CONF_PIN, "")
        )
        schema = vol.Schema(
            {
                vol.Optional(CONF_PIN, default=current_pin): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
