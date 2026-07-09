from . import __version__ as app_version

app_name = "swift_theme"
app_title = "Swift Theme"
app_publisher = "MuleRun"
app_description = "Fast, multi-scheme theme for Frappe v16 (Desk, Portal, Login)"
app_email = "hello@mulerun.com"
app_license = "MIT"

# ---- Assets included on every Desk page ----
app_include_css = [
    "/assets/swift_theme/css/swift-fonts.css",
    "/assets/swift_theme/css/swift-core.css",
    "/assets/swift_theme/css/swift-desk.css",
    "/assets/swift_theme/css/swift-perf.css",
]
app_include_js = [
    "/assets/swift_theme/js/swift-boot.js",
    "/assets/swift_theme/js/swift-theme-switcher.js",
    "/assets/swift_theme/js/swift-perf.js",
]

# ---- Assets included on public website / portal ----
web_include_css = [
    "/assets/swift_theme/css/swift-fonts.css",
    "/assets/swift_theme/css/swift-core.css",
    "/assets/swift_theme/css/swift-website.css",
]
web_include_js = [
    "/assets/swift_theme/js/swift-boot.js",
    "/assets/swift_theme/js/swift-website.js",
]

# ---- Override login page ----
website_route_rules = []

# Extend the default login template
extend_bootinfo = "swift_theme.api.boot.extend_bootinfo"

# Jinja context for website pages
website_context = {
    "favicon": "/assets/swift_theme/icons/favicon.svg",
    "splash_image": "/assets/swift_theme/icons/splash.svg",
}

# ---- Boot: inject theme preferences early ----
boot_session = "swift_theme.api.boot.boot_session"

# ---- Fixtures (ship default settings) ----
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Swift Theme"]]}
]

# ---- Installation hooks ----
after_install = "swift_theme.install.after_install"
after_migrate = ["swift_theme.install.after_migrate"]
