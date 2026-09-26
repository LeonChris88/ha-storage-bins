"""Config and options flow for Storage Bins.

The integration itself is a singleton ("Storage Bins"); individual bins
live inside its options and are fully managed here — add, edit, remove —
so nothing needs to be hand-written in Lovelace YAML again.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from . import new_bin_id
from .const import (
    ACTION_ADD,
    ACTION_DONE,
    ACTION_EDIT,
    ACTION_REMOVE,
    CONF_BINS,
    CONF_CONTENTS,
    CONF_IMAGE,
    CONF_NAME,
    DOMAIN,
)


class StorageBinsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle initial (one-time) setup of the integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Storage Bins", data={}, options={CONF_BINS: []})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return StorageBinsOptionsFlow(config_entry)


def _bin_form_schema(defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): str,
            vol.Required(
                CONF_IMAGE, default=defaults.get(CONF_IMAGE, "storage/")
            ): str,
            vol.Optional(
                CONF_CONTENTS, default=defaults.get(CONF_CONTENTS, "")
            ): str,
        }
    )


class StorageBinsOptionsFlow(config_entries.OptionsFlow):
    """Add / edit / remove bins without touching YAML."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._bins: list[dict] = list(config_entry.options.get(CONF_BINS, []))
        self._editing_id: str | None = None

    @callback
    def _bin_choices(self) -> list[SelectOptionDict]:
        return [
            SelectOptionDict(value=b["id"], label=b.get(CONF_NAME, b["id"]))
            for b in self._bins
        ]

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        menu_options = [ACTION_ADD]
        if self._bins:
            menu_options += [ACTION_EDIT, ACTION_REMOVE]
        menu_options.append(ACTION_DONE)

        return self.async_show_menu(step_id="init", menu_options=menu_options)

    async def async_step_add_bin(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            self._bins.append(
                {
                    "id": new_bin_id(),
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_IMAGE: user_input[CONF_IMAGE],
                    CONF_CONTENTS: user_input.get(CONF_CONTENTS, ""),
                }
            )
            return await self.async_step_init()

        return self.async_show_form(
            step_id="add_bin", data_schema=_bin_form_schema(), errors=errors
        )

    async def async_step_edit_bin(self, user_input: dict[str, Any] | None = None):
        if user_input is not None and "bin_id" in user_input and self._editing_id is None:
            self._editing_id = user_input["bin_id"]
            return await self.async_step_edit_bin()

        if self._editing_id is None:
            schema = vol.Schema(
                {vol.Required("bin_id"): SelectSelector(
                    SelectSelectorConfig(options=self._bin_choices())
                )}
            )
            return self.async_show_form(step_id="edit_bin", data_schema=schema)

        current = next(b for b in self._bins if b["id"] == self._editing_id)

        if user_input is not None and CONF_NAME in user_input:
            current[CONF_NAME] = user_input[CONF_NAME]
            current[CONF_IMAGE] = user_input[CONF_IMAGE]
            current[CONF_CONTENTS] = user_input.get(CONF_CONTENTS, "")
            self._editing_id = None
            return await self.async_step_init()

        return self.async_show_form(
            step_id="edit_bin", data_schema=_bin_form_schema(current)
        )

    async def async_step_remove_bin(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._bins = [b for b in self._bins if b["id"] != user_input["bin_id"]]
            return await self.async_step_init()

        schema = vol.Schema(
            {vol.Required("bin_id"): SelectSelector(
                SelectSelectorConfig(options=self._bin_choices())
            )}
        )
        return self.async_show_form(step_id="remove_bin", data_schema=schema)

    async def async_step_done(self, user_input: dict[str, Any] | None = None):
        return self.async_create_entry(title="", data={CONF_BINS: self._bins})
