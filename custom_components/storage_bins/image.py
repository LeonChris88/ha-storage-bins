"""Image platform for Storage Bins.

Each configured bin becomes an `image.*` entity. The photo is read from
`<config>/www/<image path>` - uploaded photos are stored under
`/config/www/storage_bins/` by the config flow, but any relative path
under `/config/www` works (e.g. if set via the `update_bin` service).
"""
from __future__ import annotations

import logging
import mimetypes

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_BINS, CONF_DESCRIPTION, CONF_IMAGE, CONF_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    bins = entry.options.get(CONF_BINS, [])
    async_add_entities(
        [StorageBinImage(hass, entry, b) for b in bins], update_before_add=True
    )


class StorageBinImage(ImageEntity):
    """Represents a single storage bin's photo + label."""

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, bin_config: dict) -> None:
        super().__init__(hass)
        self._entry = entry
        self._bin_id = bin_config["id"]
        self._name = bin_config.get(CONF_NAME, self._bin_id)
        self._image_path = bin_config.get(CONF_IMAGE, "")
        self._description = bin_config.get(CONF_DESCRIPTION, "")

        self._attr_unique_id = f"{entry.entry_id}_{self._bin_id}"
        self._attr_name = self._name
        self._attr_extra_state_attributes = {
            "bin_id": self._bin_id,
            "description": self._description,
        }
        self.content_type = mimetypes.guess_type(self._image_path)[0] or "image/jpeg"
        self._attr_image_last_updated = dt_util.utcnow()

    async def async_image(self) -> bytes | None:
        path = self.hass.config.path("www", self._image_path)
        try:
            return await self.hass.async_add_executor_job(_read_file, path)
        except OSError:
            _LOGGER.warning("Could not read image for bin %s at %s", self._name, path)
            return None


def _read_file(path: str) -> bytes:
    with open(path, "rb") as file:
        return file.read()
