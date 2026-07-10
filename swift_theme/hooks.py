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
    "/assets/swift_theme/js/swift-focus.js",
    "/assets/swift_theme/js/swift-perf.js",
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
extend_bootinfo = "swift_theme.api.boot.extend_bootinfo"
boot_session = "swift_theme.api.boot.boot_session"

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
