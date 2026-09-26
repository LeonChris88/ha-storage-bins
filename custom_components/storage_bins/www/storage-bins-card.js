// storage-bins-card.js
// A Lovelace card that replaces hand-written per-bin YAML: it finds every
// image.* entity created by the Storage Bins integration, lays them out
// as a numbered grid, and opens a popup with the photo + an editable
// contents field (saved via storage_bins.update_bin) on tap.
//
// Install: copy to /config/www/storage-bins-card.js, add as a Lovelace
// resource (Settings > Dashboards > Resources > + Add Resource, URL
// /local/storage-bins-card.js, type: JavaScript Module), then add a card:
//   type: custom:storage-bins-card
//   title: Storage Bins   # optional

class StorageBinsCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _bins() {
    const hass = this._hass;
    return Object.keys(hass.states)
      .filter((id) => id.startsWith("image."))
      .map((id) => hass.states[id])
      .filter((st) => st.attributes && "bin_id" in st.attributes)
      .sort((a, b) => (a.attributes.friendly_name || "").localeCompare(b.attributes.friendly_name || ""));
  }

  _openBin(entityState) {
    const hass = this._hass;
    const bin_id = entityState.attributes.bin_id;
    const overlay = document.createElement("div");
    overlay.style.cssText =
      "position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:1000;display:flex;align-items:center;justify-content:center;";

    const box = document.createElement("div");
    box.style.cssText =
      "background:var(--card-background-color,#1c1c1c);color:var(--primary-text-color,#fff);border-radius:12px;padding:16px;max-width:90vw;width:360px;box-shadow:0 8px 24px rgba(0,0,0,.4);";

    const img = document.createElement("img");
    img.src = entityState.attributes.entity_picture;
    img.style.cssText = "width:100%;border-radius:8px;display:block;margin-bottom:12px;";

    const title = document.createElement("div");
    title.textContent = entityState.attributes.friendly_name;
    title.style.cssText = "font-size:1.1em;font-weight:500;margin-bottom:8px;";

    const textarea = document.createElement("textarea");
    textarea.value = entityState.attributes.contents || "";
    textarea.rows = 3;
    textarea.style.cssText =
      "width:100%;box-sizing:border-box;border-radius:6px;padding:8px;font-family:inherit;margin-bottom:12px;background:var(--secondary-background-color,#2c2c2c);color:inherit;border:1px solid var(--divider-color,#444);";

    const row = document.createElement("div");
    row.style.cssText = "display:flex;justify-content:flex-end;gap:8px;";

    const saveBtn = document.createElement("button");
    saveBtn.textContent = "Save";
    saveBtn.style.cssText =
      "background:var(--primary-color,#03a9f4);color:#fff;border:none;border-radius:6px;padding:8px 16px;cursor:pointer;";
    saveBtn.onclick = () => {
      hass.callService("storage_bins", "update_bin", {
        bin_id,
        contents: textarea.value,
      });
      document.body.removeChild(overlay);
    };

    const closeBtn = document.createElement("button");
    closeBtn.textContent = "Close";
    closeBtn.style.cssText =
      "background:transparent;color:inherit;border:1px solid var(--divider-color,#444);border-radius:6px;padding:8px 16px;cursor:pointer;";
    closeBtn.onclick = () => document.body.removeChild(overlay);

    row.append(closeBtn, saveBtn);
    box.append(title, img, textarea, row);
    overlay.appendChild(box);
    overlay.onclick = (e) => {
      if (e.target === overlay) document.body.removeChild(overlay);
    };
    document.body.appendChild(overlay);
  }

  _render() {
    if (!this._hass) return;
    const bins = this._bins();

    if (!this._card) {
      this._card = document.createElement("ha-card");
      if (this._config.title) this._card.header = this._config.title;
      this._grid = document.createElement("div");
      this._grid.style.cssText =
        "display:grid;grid-template-columns:repeat(auto-fill,minmax(64px,1fr));gap:8px;padding:16px;";
      this._card.appendChild(this._grid);
      this.appendChild(this._card);
    }

    this._grid.innerHTML = "";
    if (bins.length === 0) {
      const empty = document.createElement("div");
      empty.textContent =
        "No bins yet - add one via the Storage Bins integration's Configure button.";
      empty.style.opacity = "0.7";
      this._grid.appendChild(empty);
      return;
    }

    bins.forEach((st) => {
      const btn = document.createElement("div");
      btn.style.cssText =
        "display:flex;flex-direction:column;align-items:center;cursor:pointer;padding:8px;border-radius:8px;";
      btn.onmouseenter = () => (btn.style.background = "var(--secondary-background-color,#2c2c2c)");
      btn.onmouseleave = () => (btn.style.background = "transparent");

      const icon = document.createElement("ha-icon");
      icon.icon = "mdi:archive";
      icon.style.cssText = "--mdc-icon-size:32px;color:var(--secondary-text-color,#999);";

      const label = document.createElement("div");
      label.textContent = st.attributes.friendly_name || st.entity_id;
      label.style.cssText = "font-size:0.8em;margin-top:4px;text-align:center;";

      btn.append(icon, label);
      btn.onclick = () => this._openBin(st);
      this._grid.appendChild(btn);
    });
  }

  getCardSize() {
    return 3;
  }
}

customElements.define("storage-bins-card", StorageBinsCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "storage-bins-card",
  name: "Storage Bins Card",
  description: "Auto-generated grid + popups for the Storage Bins integration.",
});
