from . import __version__ as app_version

app_name = "swift_theme"
app_title = "Swift Theme"
app_publisher = "Ali Khokher"
app_description = "A theming layer for Frappe v16 — twelve presets, custom colours, and a themed login page."
app_email = "iamaliraza777@gmail.com"
app_license = "MIT"

# Shown beside the app on the marketplace listing and in Frappe's app list.
# Reuses the icon already shipped for the website favicon rather than adding a
# second asset that would have to be kept in step with it.
app_logo_url = "/assets/swift_theme/icons/favicon.svg"

# ---- Desk assets ----
# Every desk stylesheet, bundled. See public/css/swift_theme.bundle.scss for
# why: a raw /assets path gets no content hash, so browsers kept serving the
# previous release's CSS and shipped fixes never reached anyone.
app_include_css = [
    "swift_theme.bundle.css",
]
app_include_js = [
    "swift_theme.bundle.js",
]

# ---- Website / portal assets ----
# The portal and login set, bundled for the same reason.
web_include_css = [
    "swift_theme_web.bundle.css",
]
web_include_js = [
    "swift_theme_web.bundle.js",
]

# ---- Form scripts ----
# The theme fields this app adds to User are only editable when the server
# would accept a change; the script keeps the form honest about that.
doctype_js = {"User": "public/js/user_form.js"}

# ---- Boot info ----
# extend_bootinfo alone is enough; also registering boot_session would compute
# the same preferences a second time on every desk load.
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
