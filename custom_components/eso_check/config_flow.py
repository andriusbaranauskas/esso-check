"""Config flow for ESO Free Capacity Check."""

from __future__ import annotations

import logging
import re
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .api import EsoApiError, fetch_capacity_status
from .const import (
    CONF_CHECK_URL,
    CONF_OBJECT_NUMBER,
    CONF_SCAN_INTERVAL,
    DEFAULT_CHECK_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

OBJECT_NUMBER_PATTERN = re.compile(r"^\d{1,8}$")


class EsoCheckFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an ESO check config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            object_number = user_input[CONF_OBJECT_NUMBER].strip()
            check_url = user_input.get(CONF_CHECK_URL, DEFAULT_CHECK_URL).strip()
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            if not OBJECT_NUMBER_PATTERN.match(object_number):
                errors["base"] = "invalid_auth"
            else:
                await self.async_set_unique_id(object_number)
                self._abort_if_unique_id_configured()

                try:
                    await validate_input(self.hass, object_number, check_url)
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except InvalidObjectNumber:
                    errors["base"] = "invalid_auth"
                except Exception:  # noqa: BLE001
                    _LOGGER.exception("Unexpected error during ESO setup")
                    errors["base"] = "unknown"
                else:
                    return self.async_create_entry(
                        title=f"ESO {object_number}",
                        data={
                            CONF_OBJECT_NUMBER: object_number,
                            CONF_CHECK_URL: check_url,
                            CONF_SCAN_INTERVAL: scan_interval,
                            CONF_NAME: f"ESO {object_number}",
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_OBJECT_NUMBER): selector.TextSelector(),
                vol.Optional(CONF_CHECK_URL, default=DEFAULT_CHECK_URL): selector.TextSelector(),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=3600,
                        max=604800,
                        step=3600,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class CannotConnect(HomeAssistantError):
    """Error to indicate connection failure."""


class InvalidObjectNumber(HomeAssistantError):
    """Error to indicate invalid object number."""


async def validate_input(
    hass: HomeAssistant, object_number: str, check_url: str
) -> dict[str, Any]:
    """Validate credentials by performing a live ESO check."""
    try:
        async with aiohttp.ClientSession() as session:
            return await fetch_capacity_status(session, check_url, object_number)
    except EsoApiError as err:
        message = str(err).lower()
        if "connect" in message or "load" in message or "query" in message:
            raise CannotConnect from err
        raise InvalidObjectNumber from err
