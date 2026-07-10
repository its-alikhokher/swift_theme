import frappe


ACCENTS = [
    {"key": "indigo",  "label": "Indigo"},
    {"key": "violet",  "label": "Violet"},
    {"key": "blue",    "label": "Blue"},
    {"key": "sky",     "label": "Sky"},
    {"key": "teal",    "label": "Teal"},
    {"key": "emerald", "label": "Emerald"},
    {"key": "amber",   "label": "Amber"},
    {"key": "rose",    "label": "Rose"},
    {"key": "pink",    "label": "Pink"},
    {"key": "slate",   "label": "Slate"},
]

FULL_THEMES = [
    {"key": "",                 "label": "None (use accent + Frappe mode)"},
    {"key": "dracula",          "label": "Dracula (dark)"},
    {"key": "nord",             "label": "Nord (dark)"},
    {"key": "solarized-light",  "label": "Solarized Light"},
    {"key": "solarized-dark",   "label": "Solarized Dark"},
    {"key": "gruvbox-dark",     "label": "Gruvbox Dark"},
    {"key": "gruvbox-light",    "label": "Gruvbox Light"},
]


def boot_session(bootinfo):
    bootinfo.swift_theme = get_effective_prefs()


def extend_bootinfo(bootinfo):
    bootinfo.swift_theme = get_effective_prefs()


@frappe.whitelist()
def get_effective_prefs():
    """User overrides > Settings default. Everything else falls back sanely."""
    s = _settings()
    u = _user_prefs()

    follow = 1 if u.get("swift_follow_frappe") is None else int(u["swift_follow_frappe"])
    mode = u.get("swift_mode") or "Follow Frappe"

    prefs = {
        # theming
        "follow_frappe": follow,
        "mode": mode,
        "accent":       u.get("swift_accent")     or s.get("default_accent")   or "indigo",
        "theme":        u.get("swift_theme")      or s.get("default_theme")    or "",
        "hex_override": s.get("brand_hex_override") or "",

        # layout
        "density":     u.get("swift_density")     or s.get("default_density")   or "Comfortable",
        "radius":      u.get("swift_radius")      or s.get("default_radius")    or "Rounded",
        "font_scale":  u.get("swift_font_scale")  or s.get("default_font_scale") or "M",
        "font_family": u.get("swift_font_family") or s.get("default_font_family") or "Inter",
        "navbar_variant":  s.get("navbar_variant")  or "Solid",
        "sidebar_variant": s.get("sidebar_variant") or "Attached",

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

        # catalog
        "accents": ACCENTS,
        "themes":  FULL_THEMES,
    }
    return prefs


@frappe.whitelist()
def set_user_pref(field, value):
    """Save a single user preference. Whitelisted subset only."""
    ALLOWED = {
        "swift_follow_frappe", "swift_mode", "swift_accent", "swift_theme",
        "swift_density", "swift_radius", "swift_font_scale", "swift_font_family",
    }
    if field not in ALLOWED:
        frappe.throw(f"Field not allowed: {field}")

    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Login required")

    frappe.db.set_value("User", user, field, value)
    return {"ok": True, "field": field, "value": value}


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
        "swift_follow_frappe", "swift_mode", "swift_accent", "swift_theme",
        "swift_density", "swift_radius", "swift_font_scale", "swift_font_family",
    ]
    try:
        row = frappe.db.get_value("User", user, fields, as_dict=True) or {}
    except Exception:
        row = {}
    return row
