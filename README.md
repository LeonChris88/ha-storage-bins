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

A private repo works fine for a custom repository — HACS just needs
your Home Assistant instance's GitHub access (or a public repo) to
pull releases; it doesn't need to be listed anywhere public.

## Push this repo to GitHub

From this folder:
```bash
git init
git add .
git commit -m "Initial commit"
gh repo create ha-storage-bins --private --source=. --remote=origin --push
```
(`gh` is the GitHub CLI; if you don't have it, create the repo on
github.com first and instead run
`git remote add origin git@github.com:<you>/ha-storage-bins.git && git push -u origin main`.)

HACS custom repositories work off tagged releases, not just the
default branch, so tag one:
```bash
git tag v0.1.0
git push origin v0.1.0
```
and create a GitHub Release from that tag (Releases → Draft a new
release) — HACS shows the latest release as the installable version.
Bump `version` in `manifest.json` and re-tag whenever you make changes.

## Migrating your existing 15 bins

You don't need to touch your current `bins.yaml` view right away — the
integration and the old dashboard can run side by side. Add each bin
through **Configure → Add Bin**, re-uploading (or re-pointing to) the
same photo you already have. Once all 15 exist, swap the old
`sections`/`bubble-card` view for the single `custom:storage-bins-card`
block above and delete the old per-bin YAML. Your navbar routing is
untouched either way — nothing here manages that.

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
