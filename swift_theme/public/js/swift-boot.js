/* Swift Theme — Boot
   Applies swift preferences to <html> ASAP (no FOUC). Keeps working alongside
   Frappe's own [data-theme] Light/Dark/Auto attribute; we NEVER touch that.
   Instead we add our own data-swift-* attributes that layer on top. */

(function () {
    var KEYS = {
        accent:       "swift_accent",
        theme:        "swift_theme_full",
        density:      "swift_density",
        radius:       "swift_radius",
        font_family:  "swift_font_family",
        font_scale:   "swift_font_scale",
        navbar:       "swift_navbar",
        sidebar:      "swift_sidebar_variant",
        perf:         "swift_perf",
        anim:         "swift_anim",
        scrollbar:    "swift_scrollbar",
        toast:        "swift_toast",
        focus:        "swift_focus",
        reading:      "swift_reading",
        hex:          "swift_hex_override",
    };

    var html = document.documentElement;

    function get(key) {
        try { return localStorage.getItem(KEYS[key]); } catch (e) { return null; }
    }
    function set(key, val) {
        try {
            if (val === null || val === undefined || val === "") localStorage.removeItem(KEYS[key]);
            else localStorage.setItem(KEYS[key], val);
        } catch (e) {}
    }
    function applyAttr(name, val) {
        if (val === null || val === undefined || val === "") html.removeAttribute("data-swift-" + name);
        else html.setAttribute("data-swift-" + name, val);
    }

    // ---- Apply from localStorage immediately ----
    applyAttr("accent",           get("accent")      || "indigo");
    applyAttr("theme",            get("theme")       || "");
    applyAttr("density",          get("density")     || "");
    applyAttr("radius",           get("radius")      || "");
    applyAttr("font",             get("font_family") || "");
    applyAttr("font-scale",       get("font_scale")  || "");
    applyAttr("navbar",           get("navbar")      || "");
    applyAttr("sidebar-variant",  get("sidebar")     || "");
    if (get("perf")      !== "off") applyAttr("perf", "on");
    if (get("anim")      === "off") applyAttr("anim", "off");
    if (get("scrollbar") !== "off") applyAttr("scrollbar", "on");
    if (get("toast")     !== "off") applyAttr("toast", "on");
    if (get("focus")     === "on")  applyAttr("focus", "on");
    if (get("reading")   === "on")  applyAttr("reading", "on");

    var hex = get("hex");
    if (hex) html.style.setProperty("--swift-accent", hex);

    // ---- Public API ----
    var API = {
        applyPrefs: function (p) {
            if (!p) return;
            if ("accent" in p)          { applyAttr("accent", p.accent); set("accent", p.accent); }
            if ("theme" in p)           { applyAttr("theme", p.theme); set("theme", p.theme); }
            if ("density" in p)         { applyAttr("density", p.density); set("density", p.density); }
            if ("radius" in p)          { applyAttr("radius", p.radius); set("radius", p.radius); }
            if ("font_family" in p)     { applyAttr("font", p.font_family); set("font_family", p.font_family); }
            if ("font_scale" in p)      { applyAttr("font-scale", p.font_scale); set("font_scale", p.font_scale); }
            if ("navbar_variant" in p)  { applyAttr("navbar", p.navbar_variant); set("navbar", p.navbar_variant); }
            if ("sidebar_variant" in p) { applyAttr("sidebar-variant", p.sidebar_variant); set("sidebar", p.sidebar_variant); }
            if ("pin_behavior" in p)    { applyAttr("pin", pinKey(p.pin_behavior)); }
            if (p.hex_override) {
                html.style.setProperty("--swift-accent", p.hex_override);
                set("hex", p.hex_override);
            }
            if (p.enable_perf_mode === 0) { applyAttr("perf", null); set("perf", "off"); }
            if (p.enable_perf_mode === 1) { applyAttr("perf", "on"); set("perf", "on"); }
            if (p.enable_styled_scrollbar === 0) { applyAttr("scrollbar", null); set("scrollbar", "off"); }
            if (p.enable_styled_scrollbar === 1) { applyAttr("scrollbar", "on"); set("scrollbar", "on"); }
            if (p.enable_toast_theming === 0) { applyAttr("toast", null); set("toast", "off"); }
            if (p.enable_toast_theming === 1) { applyAttr("toast", "on"); set("toast", "on"); }
        },
        setAccent: function (v)         { applyAttr("accent", v); set("accent", v); persist("swift_accent", v); },
        setFullTheme: function (v)      {
            applyAttr("theme", v);  set("theme", v);  persist("swift_theme", v);
            // Auto-switch Frappe's own Light/Dark mode based on theme family
            try {
                var DARK  = ["emerald","sapphire","obsidian","midnight","aurora","graphite","carbon"];
                var LIGHT = ["ivory","porcelain","rose-gold","monochrome","sandstone"];
                var mode  = DARK.indexOf(v) > -1 ? "dark" : (LIGHT.indexOf(v) > -1 ? "light" : null);
                if (mode && window.frappe && frappe.ui && frappe.ui.set_theme) {
                    frappe.ui.set_theme(mode);
                }
            } catch (e) {}
        },
        setDensity: function (v)        { applyAttr("density", v); set("density", v); persist("swift_density", v); },
        setRadius: function (v)         { applyAttr("radius", v);  set("radius", v);  persist("swift_radius", v); },
        setFontScale: function (v)      { applyAttr("font-scale", v); set("font_scale", v); persist("swift_font_scale", v); },
        setFontFamily: function (v)     { applyAttr("font", v); set("font_family", v); persist("swift_font_family", v); },
        toggleFocus: function () {
            var next = html.getAttribute("data-swift-focus") === "on" ? null : "on";
            applyAttr("focus", next); set("focus", next || "");
        },
        toggleReading: function () {
            var next = html.getAttribute("data-swift-reading") === "on" ? null : "on";
            applyAttr("reading", next); set("reading", next || "");
        },
    };
    window.SwiftTheme = API;

    function persist(field, value) {
        if (!(window.frappe && frappe.session && frappe.session.user && frappe.session.user !== "Guest")) return;
        try {
            frappe.call({
                method: "swift_theme.api.boot.set_user_pref",
                args: { field: field, value: value },
                freeze: false,
            });
        } catch (e) {}
    }

    // "Click to Pin" -> "click", so CSS can key off a short token.
    function pinKey(v) {
        var map = { "Click to Pin": "click", "Hover to Expand": "hover", "Always Expanded": "always" };
        return map[v] || "";
    }

    // ---- Sync with server-side prefs when bootinfo lands ----
    document.addEventListener("app_ready", syncFromBoot);
    document.addEventListener("DOMContentLoaded", syncFromBoot);

    function syncFromBoot() {
        var boot = window.frappe && frappe.boot && frappe.boot.swift_theme;
        if (boot) applyAll(boot);
    }

    // Applies every server-side setting. Safe to re-run at any time, which is
    // what makes saving Swift Theme Settings take effect without a reload.
    function applyAll(boot) {
        try {
            API.applyPrefs({
                accent: boot.accent,
                theme: boot.theme,
                density: boot.density,
                radius: boot.radius,
                font_family: boot.font_family,
                font_scale: boot.font_scale,
                navbar_variant: boot.navbar_variant,
                sidebar_variant: boot.sidebar_variant,
                pin_behavior: boot.pin_behavior,
                hex_override: boot.hex_override,
                enable_perf_mode: boot.enable_perf_mode,
                enable_styled_scrollbar: boot.enable_styled_scrollbar,
                enable_toast_theming: boot.enable_toast_theming,
            });

            // Auto-dark by time — skipped when the user has explicitly forced a
            // mode, otherwise it silently overrode their own choice.
            if (boot.auto_dark && !userForcedMode(boot)) {
                applyAutoDark(boot.auto_dark_start, boot.auto_dark_end);
            }

            // Custom CSS/JS injection
            injectCSS(boot.custom_css || "");
            if (boot.custom_js) injectJS(boot.custom_js);

            // Custom favicon
            if (boot.brand_favicon) {
                var link = document.querySelector("link[rel~='icon']") || document.createElement("link");
                link.rel = "icon"; link.href = boot.brand_favicon;
                document.head.appendChild(link);
            }

            window.SwiftTheme._boot = boot;

            // Let the switcher, sidebar and sound engine react to the new values.
            document.dispatchEvent(new CustomEvent("swift:prefs:applied", { detail: boot }));
        } catch (e) { console.warn("SwiftTheme sync failed", e); }
    }
    API.applyAll = applyAll;

    // ---- Live update when Swift Theme Settings is saved ----
    // The doctype's on_update broadcasts to every desk user, so a change made
    // by an admin lands on all open sessions without anyone refreshing.
    API.reload = function () {
        if (!(window.frappe && frappe.call)) return;
        return frappe.call({ method: "swift_theme.api.boot.get_effective_prefs", freeze: false })
            .then(function (r) {
                if (!r || !r.message) return;
                if (frappe.boot) frappe.boot.swift_theme = r.message;
                applyAll(r.message);
            })
            .catch(function () {});
    };

    function bindRealtime() {
        if (!(window.frappe && frappe.realtime && frappe.realtime.on)) return;
        if (bindRealtime._done) return;
        bindRealtime._done = true;
        try {
            frappe.realtime.on("swift_theme_updated", function () { API.reload(); });
        } catch (e) {}
    }
    document.addEventListener("app_ready", bindRealtime);
    if (window.frappe && frappe.after_ajax) frappe.after_ajax(bindRealtime);

    // "Force Light"/"Force Dark" on the User record, or Frappe's own desk theme
    // set to something other than Automatic, both count as a deliberate choice.
    function userForcedMode(boot) {
        var mode = boot && boot.mode;
        if (mode === "Force Light" || mode === "Force Dark") return true;
        return !(boot && boot.follow_frappe);
    }

    function applyAutoDark(start, end) {
        // Only if user hasn't overridden Frappe's theme via 'Force ...'
        if (!window.frappe || !frappe.ui || !frappe.ui.set_theme) return;
        try {
            var now = new Date();
            var mins = now.getHours() * 60 + now.getMinutes();
            var s = toMins(start), e = toMins(end);
            var inDark = (s < e) ? (mins >= s && mins < e) : (mins >= s || mins < e);
            if (frappe.ui.set_theme) frappe.ui.set_theme(inDark ? "dark" : "light");
        } catch (e) {}
    }
    function toMins(t) {
        if (!t) return 0;
        var p = String(t).split(":");
        return (+p[0]) * 60 + (+p[1] || 0);
    }

    // Replaces rather than skips, so edits to Custom CSS apply on save.
    function injectCSS(css) {
        var s = document.getElementById("swift-custom-css");
        if (!s) {
            if (!css) return;
            s = document.createElement("style");
            s.id = "swift-custom-css";
            document.head.appendChild(s);
        }
        if (s.textContent !== css) s.textContent = css;
    }
    function injectJS(js) {
        if (document.getElementById("swift-custom-js")) return;
        try {
            var s = document.createElement("script");
            s.id = "swift-custom-js";
            s.textContent = js;
            document.body.appendChild(s);
        } catch (e) {}
    }
})();
