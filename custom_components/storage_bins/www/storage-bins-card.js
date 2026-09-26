// storage-bins-card.js
// A Lovelace card that replaces hand-written per-bin YAML: it finds every
// image.* entity created by the Storage Bins integration, lays them out
// as a grid, and opens a popup with the photo + an editable description
// field (saved via storage_bins.update_bin) on tap.
//
// Config options (all optional, settable via the card's own visual
// editor - click Edit on the card - or by hand in YAML):
//   type: custom:storage-bins-card
//   title: Storage Bins        # card header
//   show_name: true            # show each bin's name under its icon
//   show_description: true     # show each bin's description under its name
//   columns: 5                 # fixed column count; omit for auto-fill

const DEFAULT_CONFIG = {
  show_name: true,
  show_description: true,
};

class StorageBinsCard extends HTMLElement {
  setConfig(config) {
    this._config = { ...DEFAULT_CONFIG, ...(config || {}) };
    // A config change (e.g. from the editor) should redraw immediately
    // rather than waiting for the next hass state tick.
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  static getStubConfig() {
    return { ...DEFAULT_CONFIG, title: "Storage Bins" };
  }

  static getConfigElement() {
    return document.createElement("storage-bins-card-editor");
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
    textarea.value = entityState.attributes.description || "";
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
        description: textarea.value,
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
    if (!this._hass || !this._config) return;
    const bins = this._bins();
    const showName = this._config.show_name !== false;
    const showDescription = this._config.show_description !== false;
    const columns = parseInt(this._config.columns, 10);

    if (!this._card) {
      this._card = document.createElement("ha-card");
      this._grid = document.createElement("div");
      this._grid.style.padding = "16px";
      this._grid.style.display = "grid";
      this._grid.style.gap = "8px";
      this._card.appendChild(this._grid);
      this.appendChild(this._card);
    }

    this._card.header = this._config.title || undefined;
    this._grid.style.gridTemplateColumns =
      columns > 0 ? `repeat(${columns}, 1fr)` : "repeat(auto-fill,minmax(64px,1fr))";

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
      btn.appendChild(icon);

      if (showName) {
        const label = document.createElement("div");
        label.textContent = st.attributes.friendly_name || st.entity_id;
        label.style.cssText = "font-size:0.8em;margin-top:4px;text-align:center;";
        btn.appendChild(label);
      }

      if (showDescription && st.attributes.description) {
        const desc = document.createElement("div");
        desc.textContent = st.attributes.description;
        desc.style.cssText =
          "font-size:0.7em;opacity:0.7;margin-top:2px;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%;";
        btn.appendChild(desc);
      }

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

// ---------------------------------------------------------------------
// Visual editor: real toggle switches for show_name / show_description,
// a number field for columns, and a text field for the title. Uses HA's
// own <ha-switch>/<ha-formfield>/<ha-textfield> elements, which are
// already globally registered by the frontend - no extra dependency.
// ---------------------------------------------------------------------
class StorageBinsCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...DEFAULT_CONFIG, ...(config || {}) };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  _render() {
    if (!this._config) return;

    this.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:16px;padding:16px 0;">
        <ha-textfield id="title" label="Title" value="${this._escape(this._config.title || "")}"></ha-textfield>
        <ha-formfield label="Show name">
          <ha-switch id="show_name" ${this._config.show_name !== false ? "checked" : ""}></ha-switch>
        </ha-formfield>
        <ha-formfield label="Show description">
          <ha-switch id="show_description" ${this._config.show_description !== false ? "checked" : ""}></ha-switch>
        </ha-formfield>
        <ha-textfield
          id="columns"
          label="Columns (blank = auto)"
          type="number"
          min="1"
          value="${this._config.columns ?? ""}"
        ></ha-textfield>
      </div>
    `;

    this.querySelector("#title").addEventListener("change", (e) =>
      this._update({ title: e.target.value || undefined })
    );
    this.querySelector("#show_name").addEventListener("change", (e) =>
      this._update({ show_name: e.target.checked })
    );
    this.querySelector("#show_description").addEventListener("change", (e) =>
      this._update({ show_description: e.target.checked })
    );
    this.querySelector("#columns").addEventListener("change", (e) => {
      const value = e.target.value ? parseInt(e.target.value, 10) : undefined;
      this._update({ columns: value });
    });
  }

  _escape(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  _update(patch) {
    this._config = { ...this._config, ...patch };
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      })
    );
  }
}

customElements.define("storage-bins-card-editor", StorageBinsCardEditor);
