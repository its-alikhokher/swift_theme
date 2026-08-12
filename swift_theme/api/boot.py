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
    {"key": "",           "label": "None (use accent + Frappe mode)"},
    {"key": "emerald",    "label": "Emerald",    "tag": "Dark · SaaS premium green"},
    {"key": "sapphire",   "label": "Sapphire",   "tag": "Dark · Enterprise banking blue"},
    {"key": "obsidian",   "label": "Obsidian",   "tag": "Dark · Developer luxury"},
    {"key": "midnight",   "label": "Midnight",   "tag": "Dark · Yacht-club navy"},
    {"key": "aurora",     "label": "Aurora",     "tag": "Dark · Glassy magic"},
    {"key": "graphite",   "label": "Graphite",   "tag": "Dark · Editorial charcoal"},
    {"key": "carbon",     "label": "Carbon",     "tag": "Dark · Terminal neon"},
    {"key": "ivory",      "label": "Ivory",      "tag": "Light · Museum-quality luxury"},
    {"key": "porcelain",  "label": "Porcelain",  "tag": "Light · Warm editorial"},
    {"key": "rose-gold",  "label": "Rose Gold",  "tag": "Light · Fashion pearl"},
    {"key": "monochrome", "label": "Monochrome", "tag": "Light · Zero color noise"},
    {"key": "sandstone",  "label": "Sandstone",  "tag": "Light · Muji calm"},
]


def boot_session(bootinfo):
    bootinfo.swift_theme = get_effective_prefs()


def extend_bootinfo(bootinfo):
    bootinfo.swift_theme = get_effective_prefs()


# Keys a signed-out visitor may see. The login page needs branding and layout;
# it has no business receiving custom CSS/JS or anything else site-internal.
GUEST_KEYS = {
    "accent", "theme", "hex_override",
    "density", "radius", "font_scale", "font_family",
    "navbar_variant", "sidebar_variant", "pin_behavior",
    "brand_name", "brand_logo", "brand_logo_dark", "brand_favicon",
    "login_layout", "login_bg_image", "login_tagline", "login_show_signup",
    "accents", "themes",
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
        "accents": ACCENTS,
        "themes":  FULL_THEMES,
    }

    if frappe.session.user == "Guest":
        return {k: v for k, v in prefs.items() if k in GUEST_KEYS}

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
        "swift_follow_frappe", "swift_mode", "swift_accent", "swift_theme",
        "swift_density", "swift_radius", "swift_font_scale", "swift_font_family",
    ]
    try:
        row = frappe.db.get_value("User", user, fields, as_dict=True) or {}
    except Exception:
        row = {}
    return row
