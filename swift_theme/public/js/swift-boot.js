/* Swift Theme — Boot
   Runs as early as possible. Applies the scheme from localStorage BEFORE
   the DOM finishes loading to prevent flash of unstyled content (FOUC). */

(function () {
    var STORAGE_KEY = "swift_theme_scheme";
    var FONT_KEY = "swift_theme_font";
    var PERF_KEY = "swift_theme_perf";
    var ANIM_KEY = "swift_theme_anim";
    var SIDEBAR_KEY = "swift_theme_sidebar";

    var html = document.documentElement;

    function apply(scheme) {
        if (!scheme) return;
        html.setAttribute("data-swift-scheme", scheme);
    }

    function applyFont(font) {
        if (font) html.setAttribute("data-swift-font", font);
    }

    // 1) Try localStorage first (instant, no round trip)
    try {
        var cached = localStorage.getItem(STORAGE_KEY);
        apply(cached || "swift-light");
        applyFont(localStorage.getItem(FONT_KEY) || "Inter");

        if (localStorage.getItem(PERF_KEY) !== "off") html.setAttribute("data-swift-perf", "on");
        if (localStorage.getItem(ANIM_KEY) === "off") html.setAttribute("data-swift-anim", "off");
        if (localStorage.getItem(SIDEBAR_KEY) === "collapsed") html.setAttribute("data-swift-sidebar", "collapsed");
    } catch (e) { /* private mode etc. */ }

    // 2) Expose a tiny API for other scripts
    window.SwiftTheme = {
        apply: function (scheme) {
            apply(scheme);
            try { localStorage.setItem(STORAGE_KEY, scheme); } catch (e) {}
        },
        setFont: function (font) {
            applyFont(font);
            try { localStorage.setItem(FONT_KEY, font); } catch (e) {}
        },
        setPerf: function (on) {
            html.setAttribute("data-swift-perf", on ? "on" : "off");
            try { localStorage.setItem(PERF_KEY, on ? "on" : "off"); } catch (e) {}
        },
        setAnim: function (on) {
            html.setAttribute("data-swift-anim", on ? "on" : "off");
            try { localStorage.setItem(ANIM_KEY, on ? "on" : "off"); } catch (e) {}
        },
        toggleSidebar: function () {
            var next = html.getAttribute("data-swift-sidebar") === "collapsed" ? "expanded" : "collapsed";
            html.setAttribute("data-swift-sidebar", next);
            try { localStorage.setItem(SIDEBAR_KEY, next); } catch (e) {}
        },
    };

    // 3) When Frappe bootinfo lands, sync with server-side prefs
    document.addEventListener("app_ready", syncFromBoot);
    document.addEventListener("DOMContentLoaded", syncFromBoot);

    function syncFromBoot() {
        try {
            var boot = window.frappe && frappe.boot && frappe.boot.swift_theme;
            if (!boot) return;
            if (boot.scheme) window.SwiftTheme.apply(boot.scheme);
            if (boot.font_family) window.SwiftTheme.setFont(boot.font_family);
            if (boot.perf_mode) window.SwiftTheme.setPerf(true);
            if (boot.reduce_animations) window.SwiftTheme.setAnim(false);
            if (boot.sidebar_collapsed) {
                html.setAttribute("data-swift-sidebar", "collapsed");
            }
            window.SwiftTheme._schemes = boot.schemes || [];
            window.SwiftTheme._enableSwitcher = !!boot.enable_switcher;
        } catch (e) { console.warn("SwiftTheme sync failed", e); }
    }
})();
