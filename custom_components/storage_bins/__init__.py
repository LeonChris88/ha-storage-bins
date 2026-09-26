"""The Storage Bins integration.

Manages a set of labeled storage bins (name, photo, contents) entirely
through the UI, so adding a new bin no longer requires hand-editing
Lovelace YAML. Each bin becomes an `image` entity; a companion sensor
exposes all bin contents for search/automation use.
"""
from __future__ import annotations

import logging
import uuid

import voluptuous as vol

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.http import StaticPathConfig

from .const import (
    ATTR_BIN_ID,
    ATTR_QUERY,
    CONF_BINS,
    CONF_CONTENTS,
    CONF_IMAGE,
    CONF_NAME,
    DOMAIN,
    PLATFORMS,
    SERVICE_SEARCH,
    SERVICE_UPDATE_BIN,
)

_LOGGER = logging.getLogger(__name__)

CARD_URL = "/storage_bins_files/storage-bins-card.js"
_frontend_registered = False

UPDATE_BIN_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BIN_ID): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_CONTENTS): cv.string,
        vol.Optional(CONF_IMAGE): cv.string,
    }
)

SEARCH_SCHEMA = vol.Schema({vol.Required(ATTR_QUERY): cv.string})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Storage Bins from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"entry": entry}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    _async_register_services(hass)
    await _async_register_frontend(hass)

    return True


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the Lovelace card from this component and auto-add it as a resource.

    Means the card just works after installing via HACS - no manual copy
    into /config/www and no manual Resources entry.
    """
    global _frontend_registered
    if _frontend_registered:
        return
    _frontend_registered = True

    card_path = hass.config.path(
        "custom_components", DOMAIN, "www", "storage-bins-card.js"
    )
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, card_path, cache_headers=False)]
        )
    except AttributeError:
        # Older HA cores (pre-2024.7) don't have async_register_static_paths.
        hass.http.register_static_path(CARD_URL, card_path, cache_headers=False)

    add_extra_js_url(hass, CARD_URL)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when bins are added/edited/removed via options flow."""
    await hass.config_entries.async_reload(entry.entry_id)


def _get_bins(entry: ConfigEntry) -> list[dict]:
    return list(entry.options.get(CONF_BINS, entry.data.get(CONF_BINS, [])))


def _async_register_services(hass: HomeAssistant) -> None:
    """Register domain services once, regardless of how many entries exist."""
    if hass.services.has_service(DOMAIN, SERVICE_UPDATE_BIN):
        return

    async def _handle_update_bin(call: ServiceCall) -> None:
        bin_id = call.data[ATTR_BIN_ID]
        for entry in hass.config_entries.async_entries(DOMAIN):
            bins = _get_bins(entry)
            for b in bins:
                if b["id"] == bin_id:
                    if CONF_NAME in call.data:
                        b[CONF_NAME] = call.data[CONF_NAME]
                    if CONF_CONTENTS in call.data:
                        b[CONF_CONTENTS] = call.data[CONF_CONTENTS]
                    if CONF_IMAGE in call.data:
                        b[CONF_IMAGE] = call.data[CONF_IMAGE]
                    hass.config_entries.async_update_entry(
                        entry, options={**entry.options, CONF_BINS: bins}
                    )
                    return
        _LOGGER.warning("No storage bin found with id %s", bin_id)

    async def _handle_search(call: ServiceCall) -> ServiceResponse:
        query = call.data[ATTR_QUERY].lower()
        matches = []
        for entry in hass.config_entries.async_entries(DOMAIN):
            for b in _get_bins(entry):
                haystack = f"{b.get(CONF_NAME, '')} {b.get(CONF_CONTENTS, '')}".lower()
                if query in haystack:
                    matches.append(
                        {
                            "id": b["id"],
                            "name": b.get(CONF_NAME),
                            "contents": b.get(CONF_CONTENTS),
                        }
                    )
        return {"matches": matches}

    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_BIN, _handle_update_bin, schema=UPDATE_BIN_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEARCH,
        _handle_search,
        schema=SEARCH_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


def new_bin_id() -> str:
    """Generate a stable id for a new bin."""
    return uuid.uuid4().hex[:8]
