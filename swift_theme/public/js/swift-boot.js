/* Swift Theme — Boot
   Applies swift preferences to <html> ASAP (no FOUC). Keeps working alongside
   Frappe's own [data-theme] Light/Dark/Auto attribute; we NEVER touch that.
   Instead we add our own data-swift-* attributes that layer on top. */

(function () {
    var KEYS = {
        preset:       "swift_preset",
        primary:      "swift_primary",
        secondary:    "swift_secondary",
        themeCss:     "swift_theme_css",
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

    // ---- Apply from localStorage immediately (no flash of unstyled theme) ----
    applyColors({
        preset: get("preset") || "",
        primary: get("primary") || "",
        secondary: get("secondary") || "",
        theme_css: get("themeCss") || "",
    });
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

    // ---- Colour scheme ----
    // Two modes, mirroring Swift Theme Settings:
    //   Theme Preset  -> load that preset's own stylesheet, nothing else
    //   Custom Colors -> no stylesheet, just the brand pair as variables
    function applyColors(c) {
        if (!c) return;

        var preset = c.preset || "";
        var primary = c.primary || "";
        var secondary = c.secondary || "";

        applyAttr("preset", preset);
        // Marks "a Swift colour scheme is active" for the shared desk styling,
        // whichever of the two modes produced it.
        if (preset || primary) html.setAttribute("data-swift-themed", "");
        else html.removeAttribute("data-swift-themed");

        swapThemeStylesheet(preset ? c.theme_css : null);

        // In preset mode the stylesheet owns the palette, so inline values are
        // cleared rather than left shadowing it.
        if (preset) {
            [
                "--swift-primary", "--swift-secondary", "--swift-accent",
                "--swift-accent-hover", "--swift-accent-soft",
                "--swift-accent-fg", "--swift-ambient",
            ].forEach(function (name) { html.style.removeProperty(name); });
        } else if (primary) {
            var second = secondary || primary;
            html.style.setProperty("--swift-primary", primary);
            html.style.setProperty("--swift-secondary", second);
            html.style.setProperty("--swift-accent", primary);
            html.style.setProperty("--swift-accent-hover", second);
            html.style.setProperty("--swift-accent-soft", rgba(primary, 0.14));
            // Preset files ship these two; in custom mode nothing else would
            // define them, leaving text on accent unreadable and the animated
            // background wash missing entirely.
            html.style.setProperty("--swift-accent-fg", readableOn(primary));
            html.style.setProperty("--swift-ambient",
                "radial-gradient(1200px 600px at 8% -10%, " + rgba(primary, 0.16) + ", transparent 60%)," +
                "radial-gradient(900px 500px at 100% 110%, " + rgba(second, 0.12) + ", transparent 60%)");
        }

        set("preset", preset);
        set("primary", primary);
        set("secondary", secondary);
        set("themeCss", (preset && c.theme_css) || "");
    }

    // One <link> that is retargeted, so switching presets never stacks
    // stylesheets and the old palette can't linger.
    function swapThemeStylesheet(href) {
        var link = document.getElementById("swift-theme-css");
        if (!href) {
            if (link) link.remove();
            return;
        }
        if (!link) {
            link = document.createElement("link");
            link.id = "swift-theme-css";
            link.rel = "stylesheet";
            document.head.appendChild(link);
        }
        if (link.getAttribute("href") !== href) link.setAttribute("href", href);
    }

    function channels(hex) {
        var m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(String(hex).trim());
        if (!m) return null;
        return [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)];
    }

    function rgba(hex, alpha) {
        var c = channels(hex);
        if (!c) return "rgba(79, 70, 229, " + alpha + ")";
        return "rgba(" + c[0] + ", " + c[1] + ", " + c[2] + ", " + alpha + ")";
    }

    function luminance(hex) {
        var c = channels(hex);
        if (!c) return 0;
        var lin = c.map(function (v) {
            v /= 255;
            return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
    }

    function contrast(a, b) {
        var la = luminance(a), lb = luminance(b);
        return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
    }

    // Black or white, whichever actually contrasts better. A luminance
    // threshold is not enough for mid-tones: gold sits just under 0.45, so a
    // cut-off picked white and rendered at 2.2:1. Mirrors colour.readable_on.
    function readableOn(hex) {
        if (!channels(hex)) return "#ffffff";
        return contrast(hex, "#0b0d12") >= contrast(hex, "#ffffff") ? "#0b0d12" : "#ffffff";
    }

    // ---- Public API ----
    var API = {
        applyColors: applyColors,
        applyPrefs: function (p) {
            if (!p) return;
            if ("preset" in p || "primary" in p) {
                applyColors({
                    preset: p.preset,
                    primary: p.primary,
                    secondary: p.secondary,
                    theme_css: p.theme_css,
                });
            }
            if ("density" in p)         { applyAttr("density", p.density); set("density", p.density); }
            if ("radius" in p)          { applyAttr("radius", p.radius); set("radius", p.radius); }
            if ("font_family" in p)     { applyAttr("font", p.font_family); set("font_family", p.font_family); }
            if ("font_scale" in p)      { applyAttr("font-scale", p.font_scale); set("font_scale", p.font_scale); }
            if ("navbar_variant" in p)  { applyAttr("navbar", p.navbar_variant); set("navbar", p.navbar_variant); }
            if ("sidebar_variant" in p) { applyAttr("sidebar-variant", p.sidebar_variant); set("sidebar", p.sidebar_variant); }
            if ("pin_behavior" in p)    { applyAttr("pin", pinKey(p.pin_behavior)); }
            if (p.enable_perf_mode === 0) { applyAttr("perf", null); set("perf", "off"); }
            if (p.enable_perf_mode === 1) { applyAttr("perf", "on"); set("perf", "on"); }
            if (p.enable_styled_scrollbar === 0) { applyAttr("scrollbar", null); set("scrollbar", "off"); }
            if (p.enable_styled_scrollbar === 1) { applyAttr("scrollbar", "on"); set("scrollbar", "on"); }
            if (p.enable_toast_theming === 0) { applyAttr("toast", null); set("toast", "off"); }
            if (p.enable_toast_theming === 1) { applyAttr("toast", "on"); set("toast", "on"); }
        },
        // Switch to a preset from the catalog in frappe.boot.swift_theme.presets.
        setPreset: function (key) {
            var catalog = (window.frappe && frappe.boot && frappe.boot.swift_theme
                && frappe.boot.swift_theme.presets) || [];
            var chosen = null;
            for (var i = 0; i < catalog.length; i++) {
                if (catalog[i].key === key) { chosen = catalog[i]; break; }
            }
            if (!chosen) return;

            applyColors({
                preset: chosen.key,
                primary: chosen.primary,
                secondary: chosen.secondary,
                theme_css: chosen.css,
            });

            // Keep Frappe's own Light/Dark in step with the preset's brightness.
            try {
                if (window.frappe && frappe.ui && frappe.ui.set_theme) {
                    frappe.ui.set_theme(chosen.mode === "dark" ? "dark" : "light");
                }
            } catch (e) {}

            persist("swift_preset", chosen.label);
            // A preset and a custom pair are mutually exclusive.
            persist("swift_primary", "");
            persist("swift_secondary", "");
        },

        // Pick your own two colours instead of a preset.
        setCustomColors: function (primary, secondary) {
            if (!primary) return;
            applyColors({ preset: "", primary: primary, secondary: secondary || primary });
            persist("swift_primary", primary);
            persist("swift_secondary", secondary || primary);
            persist("swift_preset", "");
        },

        // Drop personal choices and fall back to whatever the site is set to.
        clearPersonalTheme: function () {
            persist("swift_preset", "");
            persist("swift_primary", "");
            persist("swift_secondary", "");
            return API.reload();
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
                preset: boot.preset,
                primary: boot.primary,
                secondary: boot.secondary,
                theme_css: boot.theme_css,
                density: boot.density,
                radius: boot.radius,
                font_family: boot.font_family,
                font_scale: boot.font_scale,
                navbar_variant: boot.navbar_variant,
                sidebar_variant: boot.sidebar_variant,
                pin_behavior: boot.pin_behavior,
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
