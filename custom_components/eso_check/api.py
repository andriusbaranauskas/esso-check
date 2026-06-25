"""ESO website API client."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientResponse

from .const import NO_CAPACITY_PHRASE, XSRF_COOKIE_PREFIX, XSRF_HEADER_PREFIX

_LOGGER = logging.getLogger(__name__)

_DATA_URL_SUFFIX = "/nrdata"
_XSRF_NAME_PATTERN = re.compile(
    r"var\s+secure_xsrf_name\s*=\s*['\"]([^'\"]+)['\"]"
)
_DATA_URL_PATTERN = re.compile(r'"dataUrl"\s*:\s*"([^"]+)"')


class EsoApiError(Exception):
    """Base ESO API error."""


class EsoConnectionError(EsoApiError):
    """Connection to ESO failed."""


class EsoAuthError(EsoApiError):
    """ESO rejected the request."""


def _api_url_from_page_url(page_url: str) -> str:
    """Build the nrdata API URL from the configured page URL."""
    return urljoin(page_url.rstrip("/") + "/", "nrdata")


def _collect_xsrf_token(
    page_html: str, response: ClientResponse
) -> tuple[str, str] | None:
    """Return (cookie_name, cookie_value) for the ESO XSRF token."""
    for name, morsel in response.cookies.items():
        if name.startswith(XSRF_COOKIE_PREFIX):
            return name, morsel.value

    xsrf_name_match = _XSRF_NAME_PATTERN.search(page_html)
    if xsrf_name_match is None:
        return None

    xsrf_name = xsrf_name_match.group(1)
    for name, morsel in response.cookies.items():
        if name == xsrf_name:
            return xsrf_name, morsel.value

    return None


async def fetch_capacity_status(
    session: aiohttp.ClientSession,
    page_url: str,
    object_number: str,
) -> dict[str, Any]:
    """Fetch free-capacity status for the given object number."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; HomeAssistant/ESO-Check; +https://www.home-assistant.io/)"
        ),
        "Accept": "application/json, text/html",
    }

    try:
        async with session.get(page_url, headers=headers) as response:
            response.raise_for_status()
            page_html = await response.text()
            xsrf_match = _collect_xsrf_token(page_html, response)
    except (aiohttp.ClientError, TimeoutError) as err:
        raise EsoConnectionError(f"Failed to load ESO page: {err}") from err
    if xsrf_match is None:
        raise EsoAuthError("Could not obtain ESO session token")

    xsrf_name, xsrf_value = xsrf_match

    data_url_match = _DATA_URL_PATTERN.search(page_html)
    if data_url_match:
        data_path = data_url_match.group(1).replace("\\/", "/")
        api_url = data_path if data_path.startswith("http") else urljoin(page_url, data_path)
    else:
        api_url = _api_url_from_page_url(page_url)

    post_headers = {
        **headers,
        "Content-Type": "application/json",
        f"{XSRF_HEADER_PREFIX}{xsrf_name}": xsrf_value,
    }

    try:
        async with session.post(
            api_url,
            json={"nr": object_number},
            headers=post_headers,
        ) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError) as err:
        raise EsoConnectionError(f"Failed to query ESO API: {err}") from err

    if not isinstance(payload, dict):
        raise EsoApiError("Unexpected ESO response format")

    if not payload.get("success"):
        message = payload.get("message") or "ESO request failed"
        raise EsoAuthError(message)

    data = payload.get("data") or []
    messages = [
        item.get("text_col", "")
        for item in data
        if isinstance(item, dict) and item.get("text_col")
    ]
    combined_text = " ".join(messages)

    has_no_capacity = NO_CAPACITY_PHRASE in combined_text

    capacities: dict[str, str] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        tipas = item.get("tipas")
        galia = item.get("galia")
        if tipas and galia is not None:
            capacities[str(tipas)] = str(galia)

    return {
        "has_free_capacity": not has_no_capacity,
        "message": messages[0] if messages else "",
        "messages": messages,
        "capacities": capacities,
        "object_number": object_number,
    }
