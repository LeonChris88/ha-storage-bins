"""Config and options flow for Storage Bins.

The integration itself is a singleton ("Storage Bins"); individual bins
live inside its options and are fully managed here:

  Add Bin     -> name, description, image upload
  Modify Bin  -> pick a bin, then: edit name/description, replace image,
                 or delete the bin

so nothing needs to be hand-written in Lovelace YAML again.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    FileSelector,
    FileSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from . import async_delete_bin_images, async_save_uploaded_image, new_bin_id
from .const import (
    ACTION_ADD,
    ACTION_DONE,
    ACTION_MODIFY,
    BIN_ACTION_BACK,
    BIN_ACTION_DELETE,
    BIN_ACTION_EDIT_DETAILS,
    BIN_ACTION_REPLACE_IMAGE,
    CONF_BINS,
    CONF_DESCRIPTION,
    CONF_IMAGE,
    CONF_NAME,
    DOMAIN,
)

IMAGE_SELECTOR = FileSelector(FileSelectorConfig(accept="image/*"))


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


def _add_bin_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME): str,
            vol.Optional(CONF_DESCRIPTION, default=""): str,
            vol.Required(CONF_IMAGE): IMAGE_SELECTOR,
        }
    )


def _details_schema(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): str,
            vol.Optional(
                CONF_DESCRIPTION, default=defaults.get(CONF_DESCRIPTION, "")
            ): str,
        }
    )


class StorageBinsOptionsFlow(config_entries.OptionsFlow):
    """Add / modify bins without touching YAML."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        # Independent copies - see the comment on _get_bins() in __init__.py
        # for why mutating shared dict references breaks change detection.
        self._bins: list[dict] = [dict(b) for b in config_entry.options.get(CONF_BINS, [])]
        self._selected_id: str | None = None

    @callback
    def _bin_choices(self) -> list[SelectOptionDict]:
        return [
            SelectOptionDict(value=b["id"], label=b.get(CONF_NAME, b["id"]))
            for b in self._bins
        ]

    def _selected_bin(self) -> dict:
        return next(b for b in self._bins if b["id"] == self._selected_id)

    def _async_save(self) -> None:
        """Persist self._bins to the config entry immediately.

        Called after every add/edit/delete so nothing is lost if the
        dialog gets closed instead of reaching the final "Done" step.
        """
        self.hass.config_entries.async_update_entry(
            self._entry, options={**self._entry.options, CONF_BINS: self._bins}
        )

    # -- top menu -----------------------------------------------------

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        self._selected_id = None
        menu_options = [ACTION_ADD]
        if self._bins:
            menu_options.append(ACTION_MODIFY)
        menu_options.append(ACTION_DONE)
        return self.async_show_menu(step_id="init", menu_options=menu_options)

    # -- Add Bin --------------------------------------------------------

    async def async_step_add_bin(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            bin_id = new_bin_id()
            try:
                image_path = await async_save_uploaded_image(
                    self.hass, user_input[CONF_IMAGE], bin_id
                )
            except Exception:  # noqa: BLE001 - surface as a form error, not a crash
                errors["base"] = "image_upload_failed"
            else:
                self._bins.append(
                    {
                        "id": bin_id,
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_DESCRIPTION: user_input.get(CONF_DESCRIPTION, ""),
                        CONF_IMAGE: image_path,
                    }
                )
                self._async_save()
                return await self.async_step_init()

        return self.async_show_form(
            step_id="add_bin", data_schema=_add_bin_schema(), errors=errors
        )

    # -- Modify Bin: pick a bin, then a sub-menu -------------------------

    async def async_step_modify_bin(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._selected_id = user_input["bin_id"]
            return await self.async_step_bin_menu()

        schema = vol.Schema(
            {"bin_id": SelectSelector(SelectSelectorConfig(options=self._bin_choices()))}
        )
        return self.async_show_form(step_id="modify_bin", data_schema=schema)

    async def async_step_bin_menu(self, user_input: dict[str, Any] | None = None):
        current = self._selected_bin()
        return self.async_show_menu(
            step_id="bin_menu",
            menu_options=[
                BIN_ACTION_EDIT_DETAILS,
                BIN_ACTION_REPLACE_IMAGE,
                BIN_ACTION_DELETE,
                BIN_ACTION_BACK,
            ],
            description_placeholders={"bin_name": current.get(CONF_NAME, current["id"])},
        )

    async def async_step_edit_details(self, user_input: dict[str, Any] | None = None):
        current = self._selected_bin()
        if user_input is not None:
            current[CONF_NAME] = user_input[CONF_NAME]
            current[CONF_DESCRIPTION] = user_input.get(CONF_DESCRIPTION, "")
            self._async_save()
            return await self.async_step_init()

        return self.async_show_form(
            step_id="edit_details", data_schema=_details_schema(current)
        )

    async def async_step_replace_image(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        current = self._selected_bin()
        if user_input is not None:
            try:
                current[CONF_IMAGE] = await async_save_uploaded_image(
                    self.hass, user_input[CONF_IMAGE], current["id"]
                )
            except Exception:  # noqa: BLE001
                errors["base"] = "image_upload_failed"
            else:
                self._async_save()
                return await self.async_step_init()

        schema = vol.Schema({vol.Required(CONF_IMAGE): IMAGE_SELECTOR})
        return self.async_show_form(
            step_id="replace_image", data_schema=schema, errors=errors
        )

    async def async_step_delete_bin(self, user_input: dict[str, Any] | None = None):
        current = self._selected_bin()
        if user_input is not None:
            if user_input.get("confirm"):
                await async_delete_bin_images(self.hass, current["id"])
                self._bins = [b for b in self._bins if b["id"] != current["id"]]
                self._async_save()
            return await self.async_step_init()

        schema = vol.Schema({vol.Required("confirm", default=False): bool})
        return self.async_show_form(
            step_id="delete_bin",
            data_schema=schema,
            description_placeholders={"bin_name": current.get(CONF_NAME, current["id"])},
        )

    async def async_step_back(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_modify_bin()

    # -- Done -------------------------------------------------------------

    async def async_step_done(self, user_input: dict[str, Any] | None = None):
        return self.async_create_entry(title="", data={CONF_BINS: self._bins})
