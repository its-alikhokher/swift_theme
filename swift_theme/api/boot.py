import frappe

from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
    DEFAULT_PRESET,
    PREMIUM_THEMES,
    preset_stylesheet,
)


def preset_catalog():
    """The presets offered in the navbar switcher.

    Built from PREMIUM_THEMES so the switcher, the Settings dropdown and the
    shipped stylesheets can never drift apart.
    """
    return [
        {
            "key": data["value"],
            "label": name,
            "mode": data["mode"],
            "primary": data["colors"]["primary"],
            "secondary": data["colors"]["secondary"],
            "css": preset_stylesheet(data["value"]),
        }
        for name, data in PREMIUM_THEMES.items()
    ]


def boot_session(bootinfo):
    bootinfo.swift_theme = get_effective_prefs()


def extend_bootinfo(bootinfo):
    bootinfo.swift_theme = get_effective_prefs()


# Keys a signed-out visitor may see. The login page needs branding and layout;
# it has no business receiving custom CSS/JS or anything else site-internal.
GUEST_KEYS = {
    "color_mode", "color_source", "preset", "preset_name",
    "theme_css", "primary", "secondary", "is_dark",
    "density", "radius", "font_scale", "font_family",
    "navbar_variant", "sidebar_variant", "pin_behavior",
    "brand_name", "brand_logo", "brand_logo_dark", "brand_favicon",
    "login_layout", "login_bg_image", "login_tagline", "login_show_signup",
    "presets",
}


@frappe.whitelist(allow_guest=True)
def get_effective_prefs():
    """User overrides > Settings default. Everything else falls back sanely.

    Guest-accessible because the login page renders before a session exists,
    but guests receive only the presentation subset (see GUEST_KEYS).
    """
    s = _settings()
    u = _user_prefs()

    follow = 1 if u.get("swift_follow_frappe") is None else int(u["swift_follow_frappe"])
    mode = u.get("swift_mode") or "Follow Frappe"
    colors = _colors(s, u)

    prefs = {
        # colour — either a named preset with its own stylesheet, or a custom pair
        "follow_frappe": follow,
        "mode": mode,
        "color_mode":  colors["color_mode"],
        "color_source": colors["color_source"],
        "preset":      colors["preset"],
        "preset_name": colors["preset_name"],
        "theme_css":   colors["theme_css"],
        "primary":     colors["primary"],
        "secondary":   colors["secondary"],
        "is_dark":     colors["is_dark"],

        # layout
        "density":     u.get("swift_density")     or s.get("default_density")   or "Comfortable",
        "radius":      u.get("swift_radius")      or s.get("default_radius")    or "Rounded",
        "font_scale":  u.get("swift_font_scale")  or s.get("default_font_scale") or "M",
        "font_family": u.get("swift_font_family") or s.get("default_font_family") or "Inter",
        "navbar_variant":  s.get("navbar_variant")  or "Solid",
        "sidebar_variant": s.get("sidebar_variant") or "Attached",
        "pin_behavior":    s.get("pin_behavior")    or "Click to Pin",

        # features
        "enable_switcher":         int(s.get("enable_switcher") or 0),
        "enable_command_palette":  int(s.get("enable_command_palette") or 0),
        "enable_focus_mode":       int(s.get("enable_focus_mode") or 0),
        "enable_perf_mode":        int(s.get("enable_perf_mode") or 0),
        "enable_styled_scrollbar": int(s.get("enable_styled_scrollbar") or 0),
        "enable_toast_theming":    int(s.get("enable_toast_theming") or 0),
        "enable_print_theming":    int(s.get("enable_print_theming") or 0),

        # brand
        "brand_name":      s.get("brand_name") or "",
        "brand_logo":      s.get("brand_logo") or "",
        "brand_logo_dark": s.get("brand_logo_dark") or "",
        "brand_favicon":   s.get("brand_favicon") or "",

        # login
        "login_layout":      s.get("login_layout") or "Split",
        "login_bg_image":    s.get("login_bg_image") or "",
        "login_tagline":     s.get("login_tagline") or "",
        "login_show_signup": int(s.get("login_show_signup") or 0),

        # auto-dark
        "auto_dark":       int(s.get("enable_auto_dark") or 0),
        "auto_dark_start": str(s.get("auto_dark_start") or "19:00:00"),
        "auto_dark_end":   str(s.get("auto_dark_end") or "07:00:00"),

        # custom injection
        "custom_css": s.get("custom_css") or "",
        "custom_js":  s.get("custom_js") or "",

        # print
        "print_font_family": s.get("print_font_family") or "Inter",

        # sounds — sent whole so the desk can play without a round trip per event
        "sounds": _sound_config(s),

        # catalog
        "presets": preset_catalog(),
    }

    if frappe.session.user == "Guest":
        return {k: v for k, v in prefs.items() if k in GUEST_KEYS}

    return prefs


@frappe.whitelist()
def set_user_pref(field, value):
    """Save a single user preference. Whitelisted subset only."""
    ALLOWED = {
        "swift_follow_frappe", "swift_mode", "swift_preset",
        "swift_primary", "swift_secondary",
        "swift_density", "swift_radius", "swift_font_scale", "swift_font_family",
    }
    if field not in ALLOWED:
        frappe.throw(f"Field not allowed: {field}")

    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Login required")

    frappe.db.set_value("User", user, field, value)
    return {"ok": True, "field": field, "value": value}


def _custom_colors(primary, secondary, source):
    return {
        "color_mode": "Custom Colors",
        "color_source": source,
        "preset": None,
        "preset_name": None,
        "theme_css": None,
        "primary": primary or "#0b84f3",
        "secondary": secondary or "#0056b3",
        "is_dark": 1,
    }


def _colors(s, u):
    """Resolve the active colour scheme.

    Most specific choice wins:
      1. the user's own colour pair, picked from the navbar switcher
      2. the user's chosen preset
      3. whatever the site is configured for
    Saving a new site colour clears 1 and 2, so an admin change still lands.
    """
    if u.get("swift_primary"):
        return _custom_colors(u.get("swift_primary"), u.get("swift_secondary"), "user")

    if u.get("swift_preset"):
        return _preset_colors(u["swift_preset"], "user")

    if (s.get("color_mode") or "Theme Preset") == "Custom Colors":
        return _custom_colors(s.get("primary_color"), s.get("secondary_color"), "site")

    return _preset_colors(s.get("active_preset") or DEFAULT_PRESET, "site")


def _preset_colors(name, source):
    data = PREMIUM_THEMES.get(name) or PREMIUM_THEMES[DEFAULT_PRESET]
    return {
        "color_mode": "Theme Preset",
        "color_source": source,
        "preset": data["value"],
        "preset_name": name if name in PREMIUM_THEMES else DEFAULT_PRESET,
        "theme_css": preset_stylesheet(data["value"]),
        "primary": data["colors"]["primary"],
        "secondary": data["colors"]["secondary"],
        "is_dark": 1 if data["mode"] == "dark" else 0,
    }


def _sound_config(s):
    """Event key -> sound URL, for events that actually have a file attached."""
    if not int(s.get("enable_sounds") or 0):
        return {"enabled": 0, "volume": 0, "files": {}}

    files = {}
    for row in s.get("sound_events") or []:
        # Rows arrive as dicts from as_dict(), or as Documents when cached.
        key = row.get("event_key") if isinstance(row, dict) else row.event_key
        path = row.get("sound_file") if isinstance(row, dict) else row.sound_file
        if key and path:
            files[key] = path

    volume = min(max(int(s.get("volume_level") or 50), 0), 100) / 100.0
    return {"enabled": 1, "volume": volume, "files": files}


def _settings():
    try:
        return frappe.get_cached_doc("Swift Theme Settings", "Swift Theme Settings").as_dict()
    except Exception:
        return {}


def _user_prefs():
    user = frappe.session.user
    if not user or user == "Guest":
        return {}
    fields = [
        "swift_follow_frappe", "swift_mode", "swift_preset",
        "swift_primary", "swift_secondary",
        "swift_density", "swift_radius", "swift_font_scale", "swift_font_family",
    ]
    try:
        row = frappe.db.get_value("User", user, fields, as_dict=True) or {}
    except Exception:
        row = {}
    return row
