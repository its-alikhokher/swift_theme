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
        setFullTheme: function (v)      { applyAttr("theme", v);  set("theme", v);  persist("swift_theme", v); },
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

    // ---- Sync with server-side prefs when bootinfo lands ----
    document.addEventListener("app_ready", syncFromBoot);
    document.addEventListener("DOMContentLoaded", syncFromBoot);

    function syncFromBoot() {
        try {
            var boot = window.frappe && frappe.boot && frappe.boot.swift_theme;
            if (!boot) return;

            API.applyPrefs({
                accent: boot.accent,
                theme: boot.theme,
                density: boot.density,
                radius: boot.radius,
                font_family: boot.font_family,
                font_scale: boot.font_scale,
                navbar_variant: boot.navbar_variant,
                sidebar_variant: boot.sidebar_variant,
                hex_override: boot.hex_override,
                enable_perf_mode: boot.enable_perf_mode,
                enable_styled_scrollbar: boot.enable_styled_scrollbar,
                enable_toast_theming: boot.enable_toast_theming,
            });

            // Auto-dark by time
            if (boot.auto_dark) applyAutoDark(boot.auto_dark_start, boot.auto_dark_end);

            // Custom CSS/JS injection
            if (boot.custom_css) injectCSS(boot.custom_css);
            if (boot.custom_js)  injectJS(boot.custom_js);

            // Custom favicon
            if (boot.brand_favicon) {
                var link = document.querySelector("link[rel~='icon']") || document.createElement("link");
                link.rel = "icon"; link.href = boot.brand_favicon;
                document.head.appendChild(link);
            }

            window.SwiftTheme._boot = boot;
        } catch (e) { console.warn("SwiftTheme sync failed", e); }
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

    function injectCSS(css) {
        if (document.getElementById("swift-custom-css")) return;
        var s = document.createElement("style");
        s.id = "swift-custom-css";
        s.textContent = css;
        document.head.appendChild(s);
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
