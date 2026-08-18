/* Executes swift-boot.js against a minimal DOM stub.

   The Python suite can only assert that the server sends the right values; it
   cannot see whether the browser does anything with them. This runs the real
   file and checks the two things the CSS depends on: the data-swift-* attributes
   on <html>, and the single theme <link> being swapped rather than stacked.

   Run directly with `node`, or via the Python test that shells out to it. */

const fs = require("fs");
const vm = require("vm");

function makeElement(tag) {
    return {
        tagName: (tag || "").toUpperCase(),
        id: "",
        rel: "",
        _attrs: {},
        style: {
            _props: {},
            setProperty(k, v) { this._props[k] = v; },
            removeProperty(k) { delete this._props[k]; },
            getPropertyValue(k) { return this._props[k]; },
        },
        setAttribute(k, v) { this._attrs[k] = String(v); if (k === "href") this.href = String(v); },
        getAttribute(k) { return k in this._attrs ? this._attrs[k] : null; },
        removeAttribute(k) { delete this._attrs[k]; },
        appendChild(c) { (this.children = this.children || []).push(c); return c; },
        remove() { removed.push(this); },
        addEventListener() {},
        querySelector() { return null; },
    };
}

let removed = [];
const html = makeElement("html");
const head = makeElement("head");
const body = makeElement("body");

const store = {};
const document = {
    documentElement: html,
    head,
    body,
    readyState: "complete",
    createElement: makeElement,
    getElementById(id) {
        return (head.children || []).find((c) => c.id === id && !removed.includes(c)) || null;
    },
    querySelector() { return null; },
    addEventListener() {},
    dispatchEvent() { return true; },
};

const sandbox = {
    document,
    window: { frappe: undefined },
    localStorage: {
        getItem: (k) => (k in store ? store[k] : null),
        setItem: (k, v) => { store[k] = String(v); },
        removeItem: (k) => { delete store[k]; },
    },
    CustomEvent: function (type, init) { return { type, detail: init && init.detail }; },
    console,
    setTimeout,
    Date,
};
sandbox.window.document = document;
sandbox.window.localStorage = sandbox.localStorage;
sandbox.globalThis = sandbox;

vm.createContext(sandbox);
const bootPath = process.argv[2] ||
    require("path").join(__dirname, "..", "public", "js", "swift-boot.js");
const src = fs.readFileSync(bootPath, "utf8");
vm.runInContext(src, sandbox);

const API = sandbox.window.SwiftTheme;
const themeLink = () => document.getElementById("swift-theme-css");
const linkCount = () => (head.children || []).filter(
    (c) => c.id === "swift-theme-css" && !removed.includes(c)).length;

let pass = 0, fail = 0;
function check(label, cond, detail) {
    if (cond) { pass++; console.log("  PASS  " + label); }
    else { fail++; console.log("  FAIL  " + label + (detail ? "  -> " + detail : "")); }
}

console.log("\n== 1. Apply a preset (what saving Settings triggers) ==");
API.applyPrefs({
    preset: "ocean-depth",
    primary: "#06b6d4",
    secondary: "#0891b2",
    theme_css: "/assets/swift_theme/css/themes/ocean-depth.css",
    density: "Comfortable",
});
check("data-swift-preset set on <html>",
    html.getAttribute("data-swift-preset") === "ocean-depth", html.getAttribute("data-swift-preset"));
check("data-swift-themed set (drives the shared desk CSS)",
    html.getAttribute("data-swift-themed") !== null);
check("stylesheet <link> created with the preset href",
    themeLink() && themeLink().getAttribute("href") === "/assets/swift_theme/css/themes/ocean-depth.css",
    themeLink() && themeLink().getAttribute("href"));
check("link rel is stylesheet", themeLink() && themeLink().rel === "stylesheet");

console.log("\n== 2. Switch to another preset ==");
API.applyPrefs({
    preset: "crimson-red",
    primary: "#ef4444",
    secondary: "#dc2626",
    theme_css: "/assets/swift_theme/css/themes/crimson-red.css",
});
check("href retargeted to the new preset",
    themeLink() && themeLink().getAttribute("href") === "/assets/swift_theme/css/themes/crimson-red.css",
    themeLink() && themeLink().getAttribute("href"));
check("still exactly ONE stylesheet link (no stacking)", linkCount() === 1, "count=" + linkCount());

console.log("\n== 3. Switch to Custom Colors ==");
API.applyPrefs({ preset: null, primary: "#7C3AED", secondary: "#DB2777", theme_css: null });
check("preset attribute cleared", html.getAttribute("data-swift-preset") === null);
check("preset stylesheet removed", themeLink() === null);
check("--swift-primary set inline", html.style.getPropertyValue("--swift-primary") === "#7C3AED");
check("--swift-secondary set inline", html.style.getPropertyValue("--swift-secondary") === "#DB2777");
check("--swift-accent aliased to primary",
    html.style.getPropertyValue("--swift-accent") === "#7C3AED");
check("data-swift-themed still set for custom mode",
    html.getAttribute("data-swift-themed") !== null);

console.log("\n== 3b. Custom mode must still supply on-accent text + background wash ==");
check("--swift-accent-fg computed for contrast",
    html.style.getPropertyValue("--swift-accent-fg") === "#ffffff",
    html.style.getPropertyValue("--swift-accent-fg"));
check("--swift-ambient set (animated background needs it)",
    (html.style.getPropertyValue("--swift-ambient") || "").indexOf("radial-gradient") === 0,
    html.style.getPropertyValue("--swift-ambient"));

API.applyPrefs({ preset: null, primary: "#FFE066", secondary: "#FFD43B", theme_css: null });
check("light custom colour gets dark on-accent text",
    html.style.getPropertyValue("--swift-accent-fg") === "#0b0d12",
    html.style.getPropertyValue("--swift-accent-fg"));

// Gold sits at luminance .43 — a .45 threshold picked white, at 2.2:1.
API.applyPrefs({ preset: null, primary: "#e0a422", secondary: "#c2a878", theme_css: null });
check("mid-tone gold gets dark text, not white",
    html.style.getPropertyValue("--swift-accent-fg") === "#0b0d12",
    html.style.getPropertyValue("--swift-accent-fg"));

console.log("\n== 3c. Custom mode must paint the surfaces, not just the accent ==");
API.applyPrefs({ preset: null, primary: "#39e4a5", secondary: "#F21667",
                 theme_css: null, custom_mode: "Dark", custom_strength: "Subtle" });
const v = (n) => html.style.getPropertyValue(n);
check("--bg-color set (canvas)", !!v("--bg-color"), v("--bg-color"));
check("--card-bg set (surface)", !!v("--card-bg"), v("--card-bg"));
check("--text-color set per surface", !!v("--text-color"), v("--text-color"));
check("--border-color set", !!v("--border-color"), v("--border-color"));
check("--sidebar-bg set", !!v("--sidebar-bg"), v("--sidebar-bg"));
check("card lifts above canvas in dark", (() => {
    const lum = (h) => {
        const c = [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255)
            .map((x) => (x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4)));
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
    };
    return lum(v("--card-bg")) > lum(v("--bg-color"));
})(), v("--card-bg") + " vs " + v("--bg-color"));

const darkCanvas = v("--bg-color");
API.applyPrefs({ preset: null, primary: "#39e4a5", secondary: "#F21667",
                 theme_css: null, custom_mode: "Light", custom_strength: "Bold" });
check("Light mode gives a different canvas", v("--bg-color") !== darkCanvas,
    v("--bg-color") + " vs dark " + darkCanvas);
check("Bold puts the brand tone on the card",
    v("--card-bg").toLowerCase() === "#39e4a5", v("--card-bg"));

console.log("\n== 4. Back to a preset: inline vars must not shadow the stylesheet ==");
API.applyPrefs({
    preset: "swift-blue", primary: "#0b84f3", secondary: "#0056b3",
    theme_css: "/assets/swift_theme/css/themes/swift-blue.css",
});
check("inline --swift-primary cleared",
    html.style.getPropertyValue("--swift-primary") === undefined);
check("inline --swift-accent cleared",
    html.style.getPropertyValue("--swift-accent") === undefined);
check("inline --swift-accent-fg cleared (preset file owns it)",
    html.style.getPropertyValue("--swift-accent-fg") === undefined);
check("inline --swift-ambient cleared",
    html.style.getPropertyValue("--swift-ambient") === undefined);
check("inline surface roles cleared so the stylesheet owns them",
    html.style.getPropertyValue("--bg-color") === undefined &&
    html.style.getPropertyValue("--card-bg") === undefined,
    html.style.getPropertyValue("--bg-color") + " / " + html.style.getPropertyValue("--card-bg"));
check("stylesheet back", themeLink() && themeLink().getAttribute("href").endsWith("swift-blue.css"));

console.log("\n== 5. Persistence for the next page load (no flash) ==");
check("preset stored in localStorage", store["swift_preset"] === "swift-blue", store["swift_preset"]);
check("theme css url stored", (store["swift_theme_css"] || "").endsWith("swift-blue.css"));

console.log("\n== 6. Other preferences still applied ==");
API.applyPrefs({ density: "Compact", radius: "Pill" });
check("density attribute", html.getAttribute("data-swift-density") === "Compact");
check("radius attribute", html.getAttribute("data-swift-radius") === "Pill");
// Pinning was removed; nothing may resurrect the attribute it keyed off.
check("no pin attribute is set any more",
    html.getAttribute("data-swift-pin") === null, html.getAttribute("data-swift-pin"));

console.log("\n" + "=".repeat(46));
/* ------------------------------------------------------------------
   swift-sounds.js: the theme's sounds replace Frappe's, they don't stack.

   A source grep cannot tell whether the wrapper actually suppresses anything,
   so this runs the file and calls play_sound for real.
   ------------------------------------------------------------------ */
(function soundsDoNotDoublePlay() {
    function boot(soundsEnabled, files) {
        let frappePlayed = 0;
        const ready = [];
        const frappe = {
            boot: { swift_theme: { sounds: {
                enabled: soundsEnabled, volume: 0.5, files: files || {} } } },
            utils: { play_sound: () => { frappePlayed += 1; } },
            after_ajax: (fn) => ready.push(fn),
            ui: { form: {} },
            realtime: { on() {} },
            show_alert: () => {},
        };
        const ctx = { window: { frappe }, frappe, console, setTimeout, Date, Audio: function () {} };
        ctx.globalThis = ctx;
        vm.createContext(ctx);
        vm.runInContext(
            fs.readFileSync(bootPath.replace("swift-boot.js", "swift-sounds.js"), "utf8"), ctx);
        ready.forEach((fn) => fn());
        frappe.utils.play_sound("click");
        return frappePlayed;
    }

    const withSave = { save: "/files/save.mp3" };

    check("sounds on with a save file: Frappe's own click steps aside",
        boot(true, withSave) === 0, boot(true, withSave));
    // The app ships no audio. Suppressing regardless of that made ticking
    // Sounds silence the desk outright, which is worse than leaving it alone.
    check("sounds on but nothing attached: Frappe's own sound still plays",
        boot(true, {}) === 1, boot(true, {}));
    check("sounds off: Frappe's own sounds play as normal",
        boot(false, withSave) === 1, boot(false, withSave));
})();

/* The glass switch has to travel the same road as the backdrop: applied, and
   persisted so it survives the next load without waiting for the boot call. */
API.applyPrefs({ preset: "loki", theme_css: "/x.css", backdrop: "loki",
                 show_backdrop_through: 1 });
check("show-through sets the glass attribute",
    html.getAttribute("data-swift-glass") === "on",
    html.getAttribute("data-swift-glass"));
check("show-through is remembered for the next load",
    store.swift_glass === "on", store.swift_glass);

API.applyPrefs({ preset: "loki", theme_css: "/x.css", backdrop: "loki",
                 show_backdrop_through: 0 });
check("turning show-through off clears the attribute",
    html.getAttribute("data-swift-glass") === null,
    html.getAttribute("data-swift-glass"));
check("turning it off clears the stored value",
    !("swift_glass" in store), store.swift_glass);

/* ------------------------------------------------------------------
   Cold start with a preset already in localStorage.

   The 35 checks above all run against a module that loaded successfully, so
   none of them could see the file failing to load at all. It did: the role
   tables were declared with `var` *below* the bootstrap call that uses them,
   so a browser that had ever applied a preset hit undefined.forEach inside
   clearRoles on every load. window.SwiftTheme was then never assigned, which
   took the preset, the navbar switcher and apply-on-save down with it.

   Booted in its own context, because it has to be a first load.
   ------------------------------------------------------------------ */
(function returningVisitorBoots() {
    const attrs = {};
    const el = {
        setAttribute: (k, val) => { attrs[k] = val; },
        removeAttribute: (k) => { delete attrs[k]; },
        getAttribute: (k) => (k in attrs ? attrs[k] : null),
        style: { setProperty() {}, removeProperty() {} },
    };
    const saved = {
        swift_preset: "iron-man",
        swift_themeCss: "/assets/swift_theme/css/themes/iron-man.css",
        swift_backdrop: "iron-man",
    };
    const ctx = {
        document: {
            documentElement: el, getElementById: () => null,
            head: { appendChild() {} }, querySelector: () => null,
            createElement: () => ({ setAttribute() {}, style: {} }),
            addEventListener() {},
        },
        window: {},
        localStorage: {
            getItem: (k) => (k in saved ? saved[k] : null),
            setItem: (k, val) => { saved[k] = String(val); },
            removeItem: (k) => { delete saved[k]; },
        },
        CustomEvent: function (t, i) { return { type: t, detail: i && i.detail }; },
        console, setTimeout, Date,
    };
    ctx.window.document = ctx.document;
    ctx.globalThis = ctx;
    vm.createContext(ctx);

    let threw = null;
    try {
        vm.runInContext(src, ctx);
    } catch (e) {
        threw = e.message;
    }

    check("returning visitor: boot.js does not throw", threw === null, threw);
    check("returning visitor: SwiftTheme is published",
        !!ctx.window.SwiftTheme);
    check("returning visitor: the switcher can call setPreset",
        typeof (ctx.window.SwiftTheme || {}).setPreset === "function");
    check("returning visitor: the stored preset is applied",
        attrs["data-swift-preset"] === "iron-man", attrs["data-swift-preset"]);
    check("returning visitor: the backdrop survives the restore",
        attrs["data-swift-backdrop"] === "iron-man", attrs["data-swift-backdrop"]);
})();

console.log(`  ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
