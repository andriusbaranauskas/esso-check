"""Data update coordinator for ESO Free Capacity Check."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EsoApiError, fetch_capacity_status
from .const import CONF_CHECK_URL, CONF_OBJECT_NUMBER, CONF_SCAN_INTERVAL, DEFAULT_CHECK_URL

_LOGGER = logging.getLogger(__name__)


class EsoCheckCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch ESO free capacity data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.config_entry = entry
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL),
        )
        super().__init__(
            hass,
            _LOGGER,
            name="eso_check",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from ESO."""
        object_number = self.config_entry.data[CONF_OBJECT_NUMBER]
        page_url = self.config_entry.data.get(CONF_CHECK_URL, DEFAULT_CHECK_URL)

        try:
            async with aiohttp.ClientSession() as session:
                return await fetch_capacity_status(session, page_url, object_number)
        except EsoApiError as err:
            raise UpdateFailed(str(err)) from err
