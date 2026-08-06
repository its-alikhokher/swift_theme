from . import __version__ as app_version

app_name = "swift_theme"
app_title = "Swift Theme"
app_publisher = "MuleRun"
app_description = "Swift Theme v2 - Fast, deeply themable layer for Frappe v16 (respects Light/Dark/Auto)."
app_email = "hello@mulerun.com"
app_license = "MIT"

# ---- Desk assets ----
app_include_css = [
    "/assets/swift_theme/css/swift-fonts.css",
    "/assets/swift_theme/css/swift-base.css",
    "/assets/swift_theme/css/swift-accents.css",
    "/assets/swift_theme/css/swift-themes.css",
    "/assets/swift_theme/css/swift-layout.css",
    "/assets/swift_theme/css/swift-density.css",
    "/assets/swift_theme/css/swift-desk.css",
    "/assets/swift_theme/css/swift-scrollbar.css",
    "/assets/swift_theme/css/swift-toast.css",
    "/assets/swift_theme/css/swift-perf.css",
]
app_include_js = [
    "/assets/swift_theme/js/swift-boot.js",
    "/assets/swift_theme/js/swift-mode-observer.js",
    "/assets/swift_theme/js/swift-switcher.js",
    "/assets/swift_theme/js/swift-palette.js",
    "/assets/swift_theme/js/swift-sidebar.js",
    "/assets/swift_theme/js/swift-focus.js",
    "/assets/swift_theme/js/swift-perf.js",
    # GoldElite runtime foundation (Phase 3.1) — dependency-ordered, non-breaking.
    "/assets/swift_theme/js/goldelite/core/namespace.js",
    "/assets/swift_theme/js/goldelite/utilities/util.js",
    "/assets/swift_theme/js/goldelite/core/log.js",
    "/assets/swift_theme/js/goldelite/core/events.js",
    "/assets/swift_theme/js/goldelite/core/errors.js",
    "/assets/swift_theme/js/goldelite/core/registry.js",
    "/assets/swift_theme/js/goldelite/systems/settings.js",
    "/assets/swift_theme/js/goldelite/systems/flags.js",
    "/assets/swift_theme/js/goldelite/services/compat.js",
    # GoldElite layout engine foundation (D-003) — before lifecycle, non-breaking.
    "/assets/swift_theme/js/goldelite/systems/layout/manager.js",
    "/assets/swift_theme/js/goldelite/systems/layout/layers.js",
    "/assets/swift_theme/js/goldelite/systems/layout/regions.js",
    "/assets/swift_theme/js/goldelite/systems/layout/responsive.js",
    "/assets/swift_theme/js/goldelite/systems/layout/context.js",
    "/assets/swift_theme/js/goldelite/systems/layout/frappe-chrome.js",
    "/assets/swift_theme/js/goldelite/systems/layout/index.js",
    # GoldElite component runtime (D-004) — before lifecycle, non-breaking.
    "/assets/swift_theme/js/goldelite/systems/components.js",
    # GoldElite design token engine (D-005) — before lifecycle, non-breaking.
    "/assets/swift_theme/js/goldelite/systems/tokens/registry.js",
    "/assets/swift_theme/js/goldelite/systems/tokens/resolver.js",
    "/assets/swift_theme/js/goldelite/systems/tokens/io.js",
    "/assets/swift_theme/js/goldelite/systems/tokens/css-bridge.js",
    "/assets/swift_theme/js/goldelite/systems/tokens/index.js",
    "/assets/swift_theme/js/goldelite/core/lifecycle.js",
]

# ---- Website / portal assets ----
web_include_css = [
    "/assets/swift_theme/css/swift-fonts.css",
    "/assets/swift_theme/css/swift-base.css",
    "/assets/swift_theme/css/swift-accents.css",
    "/assets/swift_theme/css/swift-themes.css",
    "/assets/swift_theme/css/swift-website.css",
    "/assets/swift_theme/css/swift-login.css",
    "/assets/swift_theme/css/swift-scrollbar.css",
]
web_include_js = [
    "/assets/swift_theme/js/swift-boot.js",
    "/assets/swift_theme/js/swift-website.js",
]

# ---- Boot info ----
# Single boot path: extend_bootinfo only (duplicate boot_session removed).
extend_bootinfo = "swift_theme.api.boot.extend_bootinfo"

# ---- Website context (login/portal) ----
website_context = {
    "favicon": "/assets/swift_theme/icons/favicon.svg",
}

# ---- Print theming ----
# Prints load /assets/swift_theme/css/swift-print.css via a Custom HTML block
# (Injected on the fly through Print Style approach; see README.)

# ---- Fixtures ----
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Swift Theme"]]},
]

# ---- Installation ----
after_install = "swift_theme.install.after_install"
after_migrate = ["swift_theme.install.after_migrate"]
