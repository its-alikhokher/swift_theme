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
        backdrop:     "swift_backdrop",
        glass:        "swift_glass",
        roles:        "swift_roles",
        density:      "swift_density",
        radius:       "swift_radius",
        font_family:  "swift_font_family",
        font_scale:   "swift_font_scale",
        navbar:       "swift_navbar",
        sidebar:      "swift_sidebar_variant",
        sidebarFill:  "swift_sidebar_fill",
        sidebarTexture: "swift_sidebar_texture",
        sidebarGradient: "swift_sidebar_gradient",
        homePreset:     "swift_home_preset",
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

    /* Slugged the same way the colour presets are: "Honeycomb" -> "honeycomb".
       An empty value removes the attribute, which is what the desk looked like
       before any of this existed - the server sends a real design, so that only
       happens if the setting has never been saved. */
    function homePresetKey(label) {
        if (!label) return "";
        return String(label).trim().toLowerCase().replace(/\s+/g, "-");
    }

    /* Defined before the first applyColors call below, not after it.

       These are `var`s, so until their assignment runs they are undefined —
       and the bootstrap call is the first thing that happens. Any browser with
       a preset in localStorage therefore hit `undefined.forEach` inside
       clearRoles on every load, which aborted this whole file: window.SwiftTheme
       was never assigned, so no preset applied, the navbar switcher threw, and
       saving Settings could not reapply anything. */
    var ROLE_VARS = {
        canvas:      ["--swift-canvas", "--bg-color"],
        surface:     ["--swift-surface", "--card-bg", "--fg-color"],
        surface_alt: ["--swift-surface-alt", "--subtle-fg", "--sidebar-bg", "--control-bg"],
        on_canvas:   ["--swift-on-canvas", "--heading-color"],
        on_surface:  ["--swift-on-surface", "--text-color"],
        muted:       ["--text-muted", "--text-light"],
        border:      ["--border-color"],
        primary:     ["--swift-primary", "--swift-accent"],
        secondary:   ["--swift-secondary", "--swift-accent-hover"],
        on_primary:  ["--swift-accent-fg"],
    };

    var CUSTOM_VARS = (function () {
        var all = ["--swift-accent-soft", "--swift-ambient", "--navbar-bg"];
        Object.keys(ROLE_VARS).forEach(function (role) {
            all = all.concat(ROLE_VARS[role]);
        });
        return all;
    })();

    // ---- Apply immediately: frappe.boot when present, localStorage otherwise ----
    // frappe.boot is already embedded inline in the page by the time this
    // script runs — Frappe's own desk template writes `frappe.boot = {...}`
    // right before the app_include_js block this file is loaded from — and it
    // carries the resolved preset's full role set, computed server-side. Using
    // it here means the very first paint already has the true colours instead
    // of only the identifiers cached from a previous visit, with nothing to
    // fetch over the network first: without this, every refresh painted
    // Frappe's own default colour for as long as the preset's stylesheet took
    // to arrive, which is the flash a preset with strong colours makes obvious.
    var serverBoot = (window.frappe && frappe.boot && frappe.boot.swift_theme) || null;

    /* Every desk load ended with a request for /undefined. Frappe's sidebar
       header renders its apps dropdown as `<img src="${item.icon_url}">`
       whenever an item has no `icon` - and the rows Navbar Settings feeds it
       carry neither, so the fragment's image fetched literally "undefined".
       Frappe's template takes its icon branch whenever `icon` is set, so
       filling the blanks in the boot data - before the sidebar reads it -
       fixes the request without touching any Frappe file. */
    try {
        var dd = frappe.boot && frappe.boot.navbar_settings
            && frappe.boot.navbar_settings.settings_dropdown;
        (dd || []).forEach(function (item) {
            if (!item.icon && !item.icon_url) item.icon = "setting-gear";
        });
    } catch (e) { /* no boot here (website pages) - nothing to mend */ }

    /* The rest of them come from rows no data patch can reach - the header's
       own divider entries ({is_divider: true}) go through the same template
       and interpolate icon_url as the literal text "undefined". The image is
       born inside jQuery's detached parse fragment, so it never appears in
       the DOM, but the browser fetches its src anyway: one GET /undefined per
       divider per load.

       jQuery.parseHTML is the one public door every such fragment passes
       through ($(html) calls it), so the token is defused there. No sane
       markup ever means `src="undefined"` literally; it can only be an
       interpolation hole, and a transparent pixel is the faithful rendering
       of one. */
    if (window.jQuery && jQuery.parseHTML) {
        var origParseHTML = jQuery.parseHTML;
        var BLANK = "data:image/gif;base64,R0lGODlhAQABAAAAACw=";
        jQuery.parseHTML = function (data) {
            if (typeof data === "string" && data.indexOf("undefined") !== -1) {
                arguments[0] = data.replace(
                    /(\ssrc=)(["']?)(?:undefined|null)\2/g,
                    "$1$2" + BLANK + "$2"
                );
            }
            return origParseHTML.apply(this, arguments);
        };
    }
    var cachedRoles = null;
    try {
        var storedRoles = get("roles");
        if (storedRoles) cachedRoles = JSON.parse(storedRoles);
    } catch (e) { cachedRoles = null; }

    applyColors({
        preset: (serverBoot && serverBoot.preset) || get("preset") || "",
        primary: (serverBoot && serverBoot.primary) || get("primary") || "",
        secondary: (serverBoot && serverBoot.secondary) || get("secondary") || "",
        theme_css: (serverBoot && serverBoot.theme_css) || get("themeCss") || "",
        backdrop: (serverBoot && serverBoot.backdrop) || get("backdrop") || "",
        glass: serverBoot ? !!serverBoot.show_backdrop_through : get("glass") === "on",
        roles: (serverBoot && serverBoot.roles) || cachedRoles,
        mode: serverBoot && serverBoot.custom_mode,
        strength: serverBoot && serverBoot.custom_strength,
    });
    applyAttr("density",          get("density")     || "");
    applyAttr("radius",           get("radius")      || "");
    applyAttr("font",             get("font_family") || "");
    applyAttr("font-scale",       get("font_scale")  || "");
    applyAttr("navbar",           get("navbar")      || "");
    applyAttr("sidebar-variant",  get("sidebar")     || "");
    applyAttr("sidebar-fill",     get("sidebarFill") || "");
    applyAttr("sidebar-texture",  get("sidebarTexture") || "");
    applyAttr("sidebar-gradient", get("sidebarGradient") || "");
    // The home page's own look. "Follow Theme" is the absence of a preset,
    // so it is stored as "" and paints from the theme tokens as before.
    applyAttr("home-preset",      get("homePreset")     || "");
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
        // The colour field behind the desk. Blank leaves the fallback wash.
        applyAttr("backdrop", c.backdrop || "");
        // Translucent surfaces are part of the colour scheme, so they restore
        // with it rather than waiting for the boot payload to arrive.
        applyAttr("glass", c.glass ? "on" : "");
        // Marks "a Swift colour scheme is active" for the shared desk styling,
        // whichever of the two modes produced it.
        if (preset || primary) html.setAttribute("data-swift-themed", "");
        else html.removeAttribute("data-swift-themed");

        // In preset mode the stylesheet is the long-term source of truth, but
        // fetching it is a network round trip. Bridge with its own roles
        // inline right away — same mechanism as Custom Colors below — so
        // there is no window where Frappe's default colours show through,
        // then hand off to the stylesheet once it has actually loaded: inline
        // custom properties beat any stylesheet rule, so leaving the bridge in
        // place afterwards would freeze the preset and break switching to a
        // different one later. Falling back to clearRoles keeps the old
        // behaviour on the rare call that has no roles to bridge with.
        var appliedRoles = null;
        if (preset) {
            appliedRoles = c.roles || null;
            if (appliedRoles) applyRoles(appliedRoles);
            else clearRoles();
        } else if (primary) {
            // No preset stylesheet in custom mode, so the whole palette is
            // written inline — canvas and card included. Setting only the
            // accent left the surfaces on Frappe's defaults, which is why a
            // custom colour never looked like a theme.
            appliedRoles = c.roles || deriveRoles(primary, secondary, c.mode, c.strength);
            applyRoles(appliedRoles);
        }
        swapThemeStylesheet(
            preset ? c.theme_css : null,
            preset && appliedRoles ? clearRoles : undefined
        );

        set("preset", preset);
        set("primary", primary);
        set("secondary", secondary);
        set("themeCss", (preset && c.theme_css) || "");
        set("backdrop", c.backdrop || "");
        set("glass", c.glass ? "on" : "");
        // Cached so the very next load's bootstrap call above can bridge
        // correctly even before frappe.boot has had a chance to help.
        set("roles", appliedRoles ? JSON.stringify(appliedRoles) : "");
    }

    // One <link> that is retargeted, so switching presets never stacks
    // stylesheets and the old palette can't linger.
    // onReady, when given, fires once href is actually the stylesheet in
    // effect — immediately if it already was, otherwise after its load event
    // (or error, so a bridge can never be left stuck waiting on a 404).
    function swapThemeStylesheet(href, onReady) {
        var link = document.getElementById("swift-theme-css");
        if (!href) {
            if (link) link.remove();
            return;
        }
        var samePreset = link && link.getAttribute("href") === href;
        if (!link) {
            link = document.createElement("link");
            link.id = "swift-theme-css";
            link.rel = "stylesheet";
            document.head.appendChild(link);
        }
        if (!samePreset) link.setAttribute("href", href);

        if (!onReady) return;
        if (samePreset) { onReady(); return; }
        var settle = function () {
            link.removeEventListener("load", settle);
            link.removeEventListener("error", settle);
            onReady();
        };
        link.addEventListener("load", settle);
        link.addEventListener("error", settle);
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

    // Roles -> the variables the desk and Frappe itself paint with.

    function applyRoles(r) {
        if (!r) return;
        Object.keys(ROLE_VARS).forEach(function (role) {
            if (!r[role]) return;
            ROLE_VARS[role].forEach(function (name) {
                html.style.setProperty(name, r[role]);
            });
        });
        html.style.setProperty("--swift-accent-soft", rgba(r.primary, 0.14));
        html.style.setProperty("--navbar-bg", rgba(r.surface, 0.82));
        html.style.setProperty("--swift-ambient",
            "radial-gradient(1200px 600px at 8% -10%, " + rgba(r.primary, 0.16) + ", transparent 60%)," +
            "radial-gradient(900px 500px at 100% 110%, " + rgba(r.secondary, 0.12) + ", transparent 60%)");
    }

    function clearRoles() {
        CUSTOM_VARS.forEach(function (name) { html.style.removeProperty(name); });
    }

    /* Mirror of colour.derive_roles in Python, so the Settings preview can
       react to a colour picker without a round trip. A test runs both against
       the same inputs and compares, so they cannot drift apart. */
    function deriveRoles(primary, secondary, mode, strength) {
        var dark = (mode || "Dark") === "Dark";
        var bold = (strength || "Subtle") === "Bold";
        secondary = secondary || primary;
        primary = ensureReadable(primary);

        var canvas, surface, surfaceAlt, ink, border;
        if (dark) {
            canvas = mix("#070910", primary, 0.06);
            surface = bold ? ensureReadable(mix(primary, "#0a0c12", 0.55))
                           : mix(canvas, "#ffffff", 0.07);
            surfaceAlt = mix(canvas, "#ffffff", 0.11);
            ink = mix("#f2f5fa", primary, 0.07);
            border = rgba(ink, 0.14);
        } else {
            canvas = mix("#ffffff", primary, 0.035);
            surface = bold ? primary : "#ffffff";
            surfaceAlt = mix("#ffffff", primary, 0.07);
            ink = mix("#12151a", primary, 0.10);
            border = rgba(ink, 0.13);
        }

        return {
            canvas: canvas, surface: surface, surface_alt: surfaceAlt,
            on_canvas: ink, on_surface: readableOn(surface),
            muted: mix(ink, canvas, 0.45), border: border,
            primary: primary, secondary: secondary, tint: secondary,
            on_primary: readableOn(primary),
        };
    }

    function mix(base, tint, amount) {
        var a = channels(base), b = channels(tint);
        if (!a || !b) return base;
        var out = [0, 1, 2].map(function (i) {
            return Math.max(0, Math.min(255, Math.round(a[i] * (1 - amount) + b[i] * amount)));
        });
        return "#" + out.map(function (v) {
            return ("0" + v.toString(16)).slice(-2);
        }).join("");
    }

    // Some mid-tones reach 4.5:1 with neither black nor white. Nudge until one
    // does, rather than refuse the colour or ship unreadable text.
    function ensureReadable(hex, target) {
        target = target || 4.5;
        if (!channels(hex)) return hex;
        if (contrast(hex, readableOn(hex)) >= target) return hex;
        var toward = luminance(hex) > 0.18 ? "#000000" : "#ffffff";
        var candidate = hex;
        for (var step = 1; step <= 24; step++) {
            candidate = mix(hex, toward, step / 100);
            if (contrast(candidate, readableOn(candidate)) >= target) return candidate;
        }
        return candidate;
    }

    // ---- Public API ----
    var API = {
        applyColors: applyColors,
        deriveRoles: deriveRoles,
        applyPrefs: function (p) {
            if (!p) return;
            if ("preset" in p || "primary" in p) {
                applyColors({
                    preset: p.preset,
                    primary: p.primary,
                    secondary: p.secondary,
                    theme_css: p.theme_css,
                    backdrop: p.backdrop,
                    glass: p.show_backdrop_through,
                    roles: p.roles,
                    mode: p.custom_mode,
                    strength: p.custom_strength,
                });
            }
            if ("density" in p)         { applyAttr("density", p.density); set("density", p.density); }
            if ("radius" in p)          { applyAttr("radius", p.radius); set("radius", p.radius); }
            if ("font_family" in p)     { applyAttr("font", p.font_family); set("font_family", p.font_family); }
            if ("font_scale" in p)      { applyAttr("font-scale", p.font_scale); set("font_scale", p.font_scale); }
            if ("navbar_variant" in p)  { applyAttr("navbar", p.navbar_variant); set("navbar", p.navbar_variant); }
            if ("sidebar_variant" in p) { applyAttr("sidebar-variant", p.sidebar_variant); set("sidebar", p.sidebar_variant); }
            if ("sidebar_brand_fill" in p) {
                var fill = p.sidebar_brand_fill ? "brand" : "";
                applyAttr("sidebar-fill", fill);
                set("sidebarFill", fill);
            }
            if ("sidebar_texture" in p) {
                var tex = p.sidebar_texture ? "on" : "";
                applyAttr("sidebar-texture", tex);
                set("sidebarTexture", tex);
            }
            if ("custom_sidebar_gradient" in p) {
                var grad = p.custom_sidebar_gradient ? "on" : "";
                applyAttr("sidebar-gradient", grad);
                set("sidebarGradient", grad);
            }
            if ("home_preset" in p) {
                var home = homePresetKey(p.home_preset);
                applyAttr("home-preset", home);
                set("homePreset", home);
            }
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

            var boot = (window.frappe && frappe.boot && frappe.boot.swift_theme) || {};
            applyColors({
                preset: chosen.key,
                primary: chosen.primary,
                secondary: chosen.secondary,
                theme_css: chosen.css,
                backdrop: boot.backdrop_pinned ? boot.backdrop : chosen.backdrop,
                glass: boot.show_backdrop_through,
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
        setCustomColors: function (primary, secondary, mode, strength) {
            if (!primary) return;
            var boot = (window.frappe && frappe.boot && frappe.boot.swift_theme) || {};
            applyColors({
                preset: "",
                primary: primary,
                secondary: secondary || primary,
                // Fall back to whatever the site is configured for, so applying
                // a colour never silently flips the desk from Light to Dark.
                mode: mode || boot.custom_mode,
                strength: strength || boot.custom_strength,
            });
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
                sidebar_brand_fill: boot.sidebar_brand_fill,
                sidebar_texture: boot.sidebar_texture,
                custom_sidebar_gradient: boot.custom_sidebar_gradient,
                home_preset: boot.home_preset,
                roles: boot.roles,
                backdrop: boot.backdrop,
                show_backdrop_through: boot.show_backdrop_through,
                custom_mode: boot.custom_mode,
                custom_strength: boot.custom_strength,
                enable_perf_mode: boot.enable_perf_mode,
                enable_styled_scrollbar: boot.enable_styled_scrollbar,
                enable_toast_theming: boot.enable_toast_theming,
            });

            // Auto-dark by time — skipped when the user has explicitly forced a
            // mode, otherwise it silently overrode their own choice.
            if (boot.auto_dark && !userForcedMode(boot)) {
                applyAutoDark(boot.auto_dark_start, boot.auto_dark_end);
            }

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
})();
