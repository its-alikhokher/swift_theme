import frappe

from swift_theme.scripts.colour import derive_roles
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
            "key": data["slug"],
            "label": name,
            "mode": data["mode"],
            "primary": data["roles"]["primary"],
            "secondary": data["roles"]["secondary"],
            # Surface roles too, so the switcher draws a true preview card
            # rather than a flat swatch.
            "bg": data["roles"]["canvas"],
            "card": data["roles"]["surface"],
            "muted": data["roles"]["muted"],
            "css": preset_stylesheet(data["slug"]),
            "backdrop": data.get("backdrop") or "none",
        }
        for name, data in PREMIUM_THEMES.items()
    ]


# Changing the site's look is an administrative act, so the navbar switcher is
# limited to the roles that would already be allowed into Swift Theme Settings.
def can_switch_theme():
    """May this user pick a theme for themselves?

    Anyone signed in. Everything the switcher can set goes through
    set_user_pref, which writes one row - the caller's own User record - so
    choosing a theme is a personal preference like a language or a timezone,
    not an act on the site. Nothing here changes what anyone else sees.

    Whether the switcher is offered at all remains Enable Theme Switcher's job,
    site-wide. This used to be System Manager only, on top of that setting,
    which meant ticking Enable Theme Switcher appeared to do nothing for every
    ordinary user: they got Frappe's Light/Dark and none of the presets.
    """
    return 0 if frappe.session.user in (None, "Guest") else 1


def boot_session(bootinfo):
    bootinfo.swift_theme = get_effective_prefs()


def extend_bootinfo(bootinfo):
    bootinfo.swift_theme = get_effective_prefs()


def _home_boot():
    from swift_theme.api.home import _saved_layout

    s = _settings()
    if not int(s.get("enable_home_page") or 0):
        return None
    return {
        "enabled": 1,
        "greeting": int(s.get("home_greeting") or 0),
        "shortcuts": int(s.get("home_shortcuts") or 0),
        "brand_name": s.get("brand_name") or frappe.get_website_settings("app_name") or "Frappe",
        "brand_logo": s.get("brand_logo") or None,
        "layout": _saved_layout(),
        # whether fetching figures is worth a request at all
        "has_cards": 1 if [r.number_card for r in (s.get("home_cards") or []) if r.number_card] else 0,
    }


# Keys a signed-out visitor may see. The login page needs branding and layout;
# it has no business receiving custom CSS/JS or anything else site-internal.
HOME_PRESETS = ("Aurora", "Dune", "Nebula", "Abyss", "Pulse", "Horizon", "Eclipse", "Honeycomb")

GUEST_KEYS = {
    "color_mode", "color_source", "preset", "preset_name",
    "theme_css", "primary", "secondary", "is_dark", "roles",
    "backdrop", "backdrop_pinned", "enable_backdrops", "show_backdrop_through",
    "density", "radius", "font_scale", "font_family",
    "navbar_variant", "sidebar_variant", "sidebar_brand_fill", "sidebar_texture", "custom_sidebar_gradient",
    "brand_name", "brand_logo", "brand_logo_dark", "brand_favicon",
    "login_layout", "login_bg_image", "login_tagline",
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
        "roles":       colors.get("roles") or {},
        # One gate for the whole feature: off means the flat theme colour, which
        # is exactly what the "none" backdrop already draws.
        "backdrop": resolve_backdrop(
            s.get("backdrop"), colors.get("preset_backdrop"),
            is_preset=bool(colors.get("preset"))
        ) if int(s.get("enable_backdrops") or 0) else "none",
        "enable_backdrops": int(s.get("enable_backdrops") or 0),
        # Translucent surfaces, so the backdrop reads through the desk instead
        # of only showing in the gaps between panels. Tied to the same gate: the
        # field is hidden in the form when backdrops are off, so a stored 1
        # would otherwise keep applying with no control left to turn it off.
        "show_backdrop_through": int(s.get("show_backdrop_through") or 0)
        if int(s.get("enable_backdrops") or 0) else 0,
        # Only Custom Colors can pin one now — in preset mode the preset owns
        # the backdrop, so the navbar must follow each preset's own choice.
        "backdrop_pinned": 0 if colors.get("preset") else (
            1 if (s.get("backdrop") or "").strip().lower() in BACKDROPS else 0),

        # layout
        "density":     u.get("swift_density")     or s.get("default_density")   or "Comfortable",
        "radius":      u.get("swift_radius")      or s.get("default_radius")    or "Rounded",
        "font_scale":  u.get("swift_font_scale")  or s.get("default_font_scale") or "M",
        "font_family": u.get("swift_font_family") or s.get("default_font_family") or "Inter",
        "navbar_variant":  s.get("navbar_variant")  or "Solid",
        "sidebar_variant": s.get("sidebar_variant") or "Attached",
        "sidebar_brand_fill": int(s.get("sidebar_brand_fill") or 0),
        "sidebar_texture": int(s.get("sidebar_texture") or 0),
        # The home page's own look. Deliberately not a GUEST_KEY: the landing
        # is behind a login, so a signed-out visitor has no use for it. Anything
        # not in the list - a value left over from an earlier option set - falls
        # back rather than reaching the browser as an attribute matching no
        # design, which would render the page unstyled.
        "home_preset": s.get("home_preset")
        if s.get("home_preset") in HOME_PRESETS
        else HOME_PRESETS[0],
        # only meaningful without a preset - a preset owns its own pair
        "custom_sidebar_gradient": int(s.get("custom_sidebar_gradient") or 0)
        if not colors.get("preset") else 0,

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

        # auto-dark
        "auto_dark":       int(s.get("enable_auto_dark") or 0),
        "auto_dark_start": str(s.get("auto_dark_start") or "19:00:00"),
        "auto_dark_end":   str(s.get("auto_dark_end") or "07:00:00"),


        # print
        "print_font_family": s.get("print_font_family") or "Inter",

        # sounds — sent whole so the desk can play without a round trip per event
        "sounds": _sound_config(s),

        # who may use the navbar switcher
        "can_switch_theme": can_switch_theme(),

        # catalog
        "presets": preset_catalog(),

        # The landing's whole configuration, so opening the desk costs no
        # request of its own. It belongs in here rather than only in
        # extend_bootinfo: saving Swift Theme Settings makes every open session
        # call this and REPLACE frappe.boot.swift_theme with what comes back,
        # so anything added only at boot silently disappeared on the first save
        # - the landing lost its brand, its saved layout and its flags until a
        # reload. A guest never sees it: "home" is not a GUEST_KEY.
        # ...and not computed at all for a guest: the login page calls this
        # too, and a guest has no landing to configure.
        "home": _home_boot() if frappe.session.user != "Guest" else None,
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
    COLOR_FIELDS = {"swift_preset", "swift_primary", "swift_secondary"}

    if field not in ALLOWED:
        frappe.throw(frappe._("Field not allowed: {0}").format(field))

    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw(frappe._("Login required"))

    # Hiding the switcher is not enough on its own — the endpoint is reachable
    # directly, so the same restriction is enforced here.
    if field in COLOR_FIELDS and not can_switch_theme():
        frappe.throw(
            frappe._("You are not permitted to change the theme."), frappe.PermissionError
        )

    frappe.db.set_value("User", user, field, value)
    return {"ok": True, "field": field, "value": value}


# What Custom Colors can pick from, and the fallbacks any theme can use.
GENERIC_BACKDROPS = ("aurora", "mesh", "grain", "facets", "silk", "none")

# One per preset, keyed by the preset's own slug. Derived rather than listed so
# a new preset cannot end up pointing at a backdrop that was never written.
CHARACTER_BACKDROPS = tuple(
    data["slug"] for data in PREMIUM_THEMES.values() if data.get("slug")
)

BACKDROPS = GENERIC_BACKDROPS + CHARACTER_BACKDROPS


def resolve_backdrop(settings_value, preset_default, is_preset=False):
    """Which background treatment the desk gets.

    In Theme Preset mode the preset decides, full stop. The backdrop is part of
    what makes a preset that preset — Venom's grain and Thanos's aurora are as
    much its identity as the hues — so switching preset has to bring its
    backdrop with it rather than leaving a stale global choice in place.

    Custom Colors has no preset to speak for it, so there the Backdrop field in
    Settings is the choice.

    The Select stores a label ("Aurora"), the CSS keys off a slug ("aurora").
    """
    if is_preset:
        return preset_default if preset_default in BACKDROPS else "none"

    chosen = (settings_value or "").strip().lower()
    if chosen in BACKDROPS:
        return chosen
    return preset_default if preset_default in BACKDROPS else "none"


def _custom_colors(primary, secondary, source, mode="Dark", strength="Subtle"):
    """Two hexes, one full palette.

    This used to return the pair and a hardcoded is_dark=1, leaving canvas and
    card to Frappe's own defaults — so a custom colour only ever changed the
    accent, and the login page (which had its own hardcoded navy) disagreed
    with the desk. Both now read the same derived roles.
    """
    roles = derive_roles(primary or "#0b84f3", secondary or "#0056b3", mode, strength)
    return {
        "color_mode": "Custom Colors",
        "color_source": source,
        "preset": None,
        "preset_name": None,
        "theme_css": None,
        "custom_mode": mode,
        "custom_strength": strength,
        # Custom colours ship no preset, so there is no default to inherit.
        "preset_backdrop": "mesh",
        "roles": roles,
        "primary": roles["primary"],
        "secondary": roles["secondary"],
        "is_dark": 1 if mode == "Dark" else 0,
    }


def _colors(s, u):
    """Resolve the active colour scheme.

    Most specific choice wins:
      1. the user's own colour pair, picked from the navbar switcher
      2. the user's chosen preset
      3. whatever the site is configured for
    Saving a new site colour clears 1 and 2, so an admin change still lands.
    """
    mode = s.get("custom_mode") or "Dark"
    strength = s.get("custom_strength") or "Subtle"

    if u.get("swift_primary"):
        return _custom_colors(
            u.get("swift_primary"), u.get("swift_secondary"), "user", mode, strength)

    if u.get("swift_preset"):
        return _preset_colors(u["swift_preset"], "user")

    if (s.get("color_mode") or "Theme Preset") == "Custom Colors":
        return _custom_colors(
            s.get("primary_color"), s.get("secondary_color"), "site", mode, strength)

    return _preset_colors(s.get("active_preset") or DEFAULT_PRESET, "site")


def _preset_colors(name, source):
    data = PREMIUM_THEMES.get(name) or PREMIUM_THEMES[DEFAULT_PRESET]
    return {
        "color_mode": "Theme Preset",
        "color_source": source,
        "preset": data["slug"],
        "preset_name": name if name in PREMIUM_THEMES else DEFAULT_PRESET,
        "theme_css": preset_stylesheet(data["slug"]),
        "roles": data["roles"],
        "preset_backdrop": data.get("backdrop") or "none",
        "primary": data["roles"]["primary"],
        "secondary": data["roles"]["secondary"],
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
