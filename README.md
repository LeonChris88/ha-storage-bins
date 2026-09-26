# Storage Bins for Home Assistant

Manage labeled storage bins (photo + description) entirely from the UI —
no more hand-editing Lovelace YAML every time you add or repack a bin.

This is scoped to the bins themselves only — it doesn't touch your
navbar-card dashboard routing at all; that stays exactly as you have it.

Replaces a manual pattern of one `bubble-card` pop-up + one
`mushroom-template-card` per bin with:

- A config flow: **Settings → Devices & Services → Add Integration →
  Storage Bins**, then use its **Configure** button:
  - **Add Bin** — Name, Description, Image (upload a photo straight
    from your browser/phone; no file paths to type).
  - **Modify Bin** — pick a bin, then Name/Description, Replace Image,
    or Delete Bin.
- One `image.*` entity per bin. Uploaded photos are stored under
  `/config/www/storage_bins/<bin id>.<ext>` automatically — replacing
  an image or deleting a bin cleans up the old file too.
- `sensor.storage_bins_index` — one sensor with every bin's name +
  description in its attributes, for search/automations.
- Two services:
  - `storage_bins.update_bin` — update a bin's name/image/description
    programmatically (e.g. from a voice assistant intent).
  - `storage_bins.search` — returns matching bins for a text query
    (response data, usable in scripts/automations).
- `storage-bins-card.js` — a Lovelace card that reads all bin entities
  and renders the grid + tap-to-view/edit popup automatically. Adding a
  bin through Configure makes it appear on the card immediately; you
  never touch dashboard YAML again. The integration serves this file
  itself and registers it as a frontend resource on startup, so there's
  nothing to copy into `/config/www` and no manual Resources entry.

## Install via HACS (custom repository, not the public store)

1. Push this repo to GitHub (see below) — private or public both work.
2. In Home Assistant: **HACS → the ⋮ menu (top right) → Custom
   repositories.**
3. Paste your repo URL, set category **Integration**, click **Add**.
4. Find "Storage Bins" in HACS → Integrations → **+ Explore & Download
   Repositories**, install it, then restart Home Assistant.
5. **Settings → Devices & Services → Add Integration → Storage Bins.**
6. Click **Configure** on the new entry → **Add Bin**, give it a name,
   an optional description, and upload a photo for it.
7. Add a card to your dashboard:
   ```yaml
   type: custom:storage-bins-card
   title: Storage Bins
   ```

## Notes / things to sanity-check before relying on this

- I wrote this against current core APIs (`ImageEntity`, `FileSelector`
  + `file_upload.process_uploaded_file`, options-flow menus with
  `description_placeholders`, service response data) but haven't run
  it against a live HA instance — test in a dev/test instance (or at
  least `ha core check_config` after installing) before replacing your
  real dashboard, especially given your history with the recorder DB.
- The `file_upload` dependency in `manifest.json` means HA sets that
  integration up automatically; no action needed on your end.
- The options flow keeps the whole bin list in one config entry. Fine
  for 15–30 bins; if you ever want per-bin devices/areas, that'd need
  restructuring to subentries (HA 2024.11+) instead.
- `update_bin` and `search` match on the config entry's in-memory
  options; if you ever run multiple Storage Bins entries the search
  spans all of them, which is intended but worth knowing.

## If you later want it in the public HACS store

Not needed for your own use, but if you ever do: add a `LICENSE` file,
make the repo public, and open a PR against
[hacs/default](https://github.com/hacs/default) — it goes through
HACS's automated validation plus a brands submission via
[home-assistant/brands](https://github.com/home-assistant/brands) for
the icon/logo. Your custom-repository install above keeps working
exactly the same either way.
