import frappe


DEFAULT_SCHEMES = [
    {"name": "Swift Light",   "key": "swift-light",   "is_dark": 0},
    {"name": "Swift Dark",    "key": "swift-dark",    "is_dark": 1},
    {"name": "Ocean Blue",    "key": "ocean-blue",    "is_dark": 0},
    {"name": "Nord",          "key": "nord",          "is_dark": 1},
    {"name": "Dracula",       "key": "dracula",       "is_dark": 1},
    {"name": "Solarized",     "key": "solarized",     "is_dark": 0},
    {"name": "Forest",        "key": "forest",        "is_dark": 0},
]


def after_install():
    _ensure_user_theme_field()
    _seed_settings()
    frappe.db.commit()


def after_migrate():
    _ensure_user_theme_field()
    _seed_settings()


def _ensure_user_theme_field():
    """Add a per-user 'Swift Theme' selector on the User doctype."""
    fieldname = "swift_theme_scheme"
    if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": fieldname}):
        return

    options = "\n".join([""] + [s["key"] for s in DEFAULT_SCHEMES])
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "User",
        "module": "Swift Theme",
        "fieldname": fieldname,
        "label": "Swift Theme",
        "fieldtype": "Select",
        "options": options,
        "insert_after": "desk_theme",
        "description": "Choose your personal Swift Theme color scheme",
    }).insert(ignore_permissions=True)


def _seed_settings():
    """Create the singleton Swift Theme Settings if missing."""
    if not frappe.db.exists("DocType", "Swift Theme Settings"):
        return
    if not frappe.db.exists("Swift Theme Settings", "Swift Theme Settings"):
        doc = frappe.get_doc({
            "doctype": "Swift Theme Settings",
            "default_scheme": "swift-light",
            "enable_theme_switcher": 1,
            "enable_perf_mode": 1,
            "sidebar_collapsed_default": 0,
            "reduce_animations": 0,
            "font_family": "Inter",
        })
        doc.insert(ignore_permissions=True)
