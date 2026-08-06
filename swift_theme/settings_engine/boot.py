"""Canonical boot assembly — the single path that produces the boot payload.

``extend_bootinfo`` is the only hook that populates ``bootinfo.swift_theme``.
The payload shape is unchanged from the v2 engine (backward compatible with
swift-boot.js / swift-website.js) but every value now comes from the
canonical adapter, so legacy storage never leaks through.
"""

import frappe

from swift_theme.settings_engine import adapter, schema

FEATURE_FIELDS = [
    "enable_switcher",
    "enable_command_palette",
    "enable_focus_mode",
    "enable_perf_mode",
    "enable_styled_scrollbar",
    "enable_toast_theming",
    "enable_print_theming",
]


def user_values():
    """Raw per-user override row (Guest/unknown users get no overrides)."""
    user = frappe.session.user
    if not user or user == "Guest":
        return {}
    fields = list(schema.USER_FIELD_SPECS.keys())
    try:
        row = frappe.db.get_value("User", user, fields, as_dict=True) or {}
    except Exception:
        row = {}
    return row


def _site(name):
    """Site-level canonical default for a setting (never None)."""
    return adapter.get(name)


def assemble():
    """Effective canonical settings for the current session.

    Resolution order: sanitized per-user override > canonical site setting
    > schema default. Output keys match the legacy v2 payload exactly.
    """
    u = user_values()
    site = _site

    def user(field, fallback):
        return adapter.effective_user_pref(field, u, fallback)

    prefs = {
        # theming
        "follow_frappe": int(user("swift_follow_frappe", 1)),
        "mode": user("swift_mode", "Follow Frappe"),
        "accent": user("swift_accent", "") or site("default_accent"),
        "theme": user("swift_theme", "") or site("default_theme"),
        "hex_override": site("brand_hex_override"),

        # layout
        "density": user("swift_density", "") or site("default_density"),
        "radius": user("swift_radius", "") or site("default_radius"),
        "font_scale": user("swift_font_scale", "") or site("default_font_scale"),
        "font_family": user("swift_font_family", "") or site("default_font_family"),
        "navbar_variant": site("navbar_variant"),
        "sidebar_variant": site("sidebar_variant"),

        # features
        "enable_switcher": int(site("enable_switcher") or 0),
        "enable_command_palette": int(site("enable_command_palette") or 0),
        "enable_focus_mode": int(site("enable_focus_mode") or 0),
        "enable_perf_mode": int(site("enable_perf_mode") or 0),
        "enable_styled_scrollbar": int(site("enable_styled_scrollbar") or 0),
        "enable_toast_theming": int(site("enable_toast_theming") or 0),
        "enable_print_theming": int(site("enable_print_theming") or 0),

        # brand
        "brand_name": site("brand_name"),
        "brand_logo": site("brand_logo"),
        "brand_logo_dark": site("brand_logo_dark"),
        "brand_favicon": site("brand_favicon"),

        # login
        "login_layout": site("login_layout"),
        "login_bg_image": site("login_bg_image"),
        "login_tagline": site("login_tagline"),
        "login_show_signup": int(site("login_show_signup") or 0),

        # auto-dark
        "auto_dark": int(site("enable_auto_dark") or 0),
        "auto_dark_start": str(site("auto_dark_start") or "19:00:00"),
        "auto_dark_end": str(site("auto_dark_end") or "07:00:00"),

        # custom injection
        "custom_css": site("custom_css"),
        "custom_js": site("custom_js"),

        # print
        "print_font_family": site("print_font_family"),

        # catalog
        "accents": schema.accent_catalog(),
        "themes": schema.theme_catalog(),

        # canonical marker (additive; ignored by legacy consumers)
        "schema_version": schema.SCHEMA_VERSION,
    }
    return prefs
