"""Constants for the Storage Bins integration."""

DOMAIN = "storage_bins"
PLATFORMS = ["image", "sensor"]

CONF_BINS = "bins"
CONF_BIN_ID = "id"
CONF_NAME = "name"
CONF_IMAGE = "image"
CONF_CONTENTS = "contents"

# Actions shown in the options-flow menu
ACTION_ADD = "add_bin"
ACTION_EDIT = "edit_bin"
ACTION_REMOVE = "remove_bin"
ACTION_DONE = "done"

SERVICE_UPDATE_BIN = "update_bin"
SERVICE_SEARCH = "search"

ATTR_BIN_ID = "bin_id"
ATTR_QUERY = "query"
