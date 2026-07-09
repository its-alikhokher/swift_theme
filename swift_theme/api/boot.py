import frappe


def boot_session(bootinfo):
    """Attach Swift Theme prefs to bootinfo so JS can apply theme without extra RPC."""
    bootinfo.swift_theme = get_effective_prefs()


def extend_bootinfo(bootinfo):
    bootinfo.swift_theme = get_effective_prefs()


@frappe.whitelist()
def get_effective_prefs():
    """Return the effective (user > settings > default) theme preferences."""
    settings = _get_settings()
    user = frappe.session.user

    user_scheme = None
    if user and user != "Guest":
        user_scheme = frappe.db.get_value("User", user, "swift_theme_scheme")

    return {
        "scheme": user_scheme or settings.get("default_scheme") or "swift-light",
        "enable_switcher": int(settings.get("enable_theme_switcher") or 0),
        "perf_mode": int(settings.get("enable_perf_mode") or 0),
        "sidebar_collapsed": int(settings.get("sidebar_collapsed_default") or 0),
        "reduce_animations": int(settings.get("reduce_animations") or 0),
        "font_family": settings.get("font_family") or "Inter",
        "schemes": _list_schemes(),
    }


@frappe.whitelist()
def set_user_scheme(scheme):
    """Save the current user's preferred scheme."""
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Login required")

    valid = {s["key"] for s in _list_schemes()}
    if scheme not in valid:
        frappe.throw(f"Unknown scheme: {scheme}")

    frappe.db.set_value("User", user, "swift_theme_scheme", scheme)
    return {"ok": True, "scheme": scheme}


def _get_settings():
    try:
        return frappe.get_cached_doc("Swift Theme Settings", "Swift Theme Settings").as_dict()
    except Exception:
        return {}


def _list_schemes():
    return [
        {"key": "swift-light", "label": "Swift Light",  "dark": False},
        {"key": "swift-dark",  "label": "Swift Dark",   "dark": True},
        {"key": "ocean-blue",  "label": "Ocean Blue",   "dark": False},
        {"key": "nord",        "label": "Nord",         "dark": True},
        {"key": "dracula",     "label": "Dracula",      "dark": True},
        {"key": "solarized",   "label": "Solarized",    "dark": False},
        {"key": "forest",      "label": "Forest",       "dark": False},
    ]
