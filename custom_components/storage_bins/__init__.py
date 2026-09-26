"""The Storage Bins integration.

Manages a set of labeled storage bins (name, photo, description)
entirely through the UI, so adding a new bin no longer requires
hand-editing Lovelace YAML. Each bin becomes an `image` entity; a
companion sensor exposes all bin descriptions for search/automation use.
"""
from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

import voluptuous as vol

from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.http import StaticPathConfig

from .const import (
    ATTR_BIN_ID,
    ATTR_QUERY,
    CONF_BINS,
    CONF_DESCRIPTION,
    CONF_IMAGE,
    CONF_NAME,
    DOMAIN,
    IMAGE_SUBDIR,
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
        vol.Optional(CONF_DESCRIPTION): cv.string,
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


# ---------------------------------------------------------------------------
# Image storage helpers - used by the config/options flow when a photo is
# uploaded through the FileSelector, and when a bin's image is replaced or
# the bin is deleted (so we don't leave orphaned files under /config/www).
# ---------------------------------------------------------------------------

def _storage_dir(hass: HomeAssistant) -> Path:
    path = Path(hass.config.path("www", IMAGE_SUBDIR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_uploaded_image_sync(hass: HomeAssistant, file_id: str, bin_id: str) -> str:
    """Copy an uploaded file into permanent storage. Returns the relative path."""
    with process_uploaded_file(hass, file_id) as temp_path:
        suffix = Path(temp_path).suffix or ".jpg"
        dest = _storage_dir(hass) / f"{bin_id}{suffix}"
        shutil.copy(temp_path, dest)
    return f"{IMAGE_SUBDIR}/{dest.name}"


async def async_save_uploaded_image(hass: HomeAssistant, file_id: str, bin_id: str) -> str:
    """Persist an uploaded image for a bin, replacing any prior file for that bin."""
    await async_delete_bin_images(hass, bin_id)
    return await hass.async_add_executor_job(
        _save_uploaded_image_sync, hass, file_id, bin_id
    )


def _delete_bin_images_sync(hass: HomeAssistant, bin_id: str) -> None:
    for existing in _storage_dir(hass).glob(f"{bin_id}.*"):
        try:
            existing.unlink()
        except OSError:
            _LOGGER.debug("Could not remove old image %s", existing)


async def async_delete_bin_images(hass: HomeAssistant, bin_id: str) -> None:
    """Remove any stored image file(s) for a bin (called on replace/delete)."""
    await hass.async_add_executor_job(_delete_bin_images_sync, hass, bin_id)


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
                    if CONF_DESCRIPTION in call.data:
                        b[CONF_DESCRIPTION] = call.data[CONF_DESCRIPTION]
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
                haystack = f"{b.get(CONF_NAME, '')} {b.get(CONF_DESCRIPTION, '')}".lower()
                if query in haystack:
                    matches.append(
                        {
                            "id": b["id"],
                            "name": b.get(CONF_NAME),
                            "description": b.get(CONF_DESCRIPTION),
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
