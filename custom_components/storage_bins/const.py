"""Constants for the Storage Bins integration."""

DOMAIN = "storage_bins"
PLATFORMS = ["image", "sensor"]

CONF_BINS = "bins"
CONF_BIN_ID = "id"
CONF_NAME = "name"
CONF_IMAGE = "image"
CONF_DESCRIPTION = "description"

# Where bin photos are stored, relative to /config/www
IMAGE_SUBDIR = "storage_bins"

# Actions shown in the options-flow menus
ACTION_ADD = "add_bin"
ACTION_MODIFY = "modify_bin"
ACTION_DONE = "done"

BIN_ACTION_EDIT_DETAILS = "edit_details"
BIN_ACTION_REPLACE_IMAGE = "replace_image"
BIN_ACTION_DELETE = "delete_bin"
BIN_ACTION_BACK = "back"

SERVICE_UPDATE_BIN = "update_bin"
SERVICE_SEARCH = "search"

ATTR_BIN_ID = "bin_id"
ATTR_QUERY = "query"
