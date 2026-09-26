"""A single 'index' sensor listing every bin's name + contents.

Handy for a search/autocomplete card, or a template like:
  {{ state_attr('sensor.storage_bins_index','bins')
       | selectattr('contents','search','flashlight')
       | list }}
"""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_BINS, CONF_CONTENTS, CONF_NAME, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([StorageBinsIndexSensor(entry)])


class StorageBinsIndexSensor(SensorEntity):
    """Sensor holding a summary of all bins, for search/automations."""

    _attr_has_entity_name = True
    _attr_name = "Storage Bins Index"
    _attr_icon = "mdi:archive-search"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_index"

    @property
    def native_value(self) -> int:
        return len(self._entry.options.get(CONF_BINS, []))

    @property
    def extra_state_attributes(self) -> dict:
        bins = self._entry.options.get(CONF_BINS, [])
        return {
            "bins": [
                {
                    "id": b["id"],
                    "name": b.get(CONF_NAME),
                    "contents": b.get(CONF_CONTENTS, ""),
                }
                for b in bins
            ]
        }
