import frappe


ACCENTS = ["indigo", "violet", "blue", "sky", "teal", "emerald", "amber", "rose", "pink", "slate"]
THEMES = ["", "dracula", "nord", "solarized-light", "solarized-dark", "gruvbox-dark", "gruvbox-light"]
MODES = ["Follow Frappe", "Force Light", "Force Dark", "Auto (time-based)"]
DENSITIES = ["Compact", "Comfortable", "Cozy"]
RADII = ["Sharp", "Rounded", "Pill"]
FONT_SCALES = ["S", "M", "L", "XL"]
FONT_FAMILIES = ["Inter", "Poppins", "Manrope", "Roboto", "System"]

USER_FIELDS = [
    ("swift_follow_frappe", "Check",  "Follow Frappe's Theme Mode", None, "1"),
    ("swift_mode",          "Select", "Swift Mode Override",         "\n".join(MODES), "Follow Frappe"),
    ("swift_accent",        "Select", "Swift Accent",                "\n".join([""] + ACCENTS), ""),
    ("swift_theme",         "Select", "Swift Full Theme (overrides accent)", "\n".join(THEMES), ""),
    ("swift_density",       "Select", "Swift Density",               "\n".join([""] + DENSITIES), ""),
    ("swift_radius",        "Select", "Swift Shape",                 "\n".join([""] + RADII), ""),
    ("swift_font_scale",    "Select", "Swift Font Scale",            "\n".join([""] + FONT_SCALES), ""),
    ("swift_font_family",   "Select", "Swift Font Family",           "\n".join([""] + FONT_FAMILIES), ""),
]


def after_install():
    _ensure_user_fields()
    _seed_settings()
    frappe.db.commit()


def after_migrate():
    _ensure_user_fields()
    _seed_settings()


def _ensure_user_fields():
    insert_after = "desk_theme"
    for fieldname, fieldtype, label, options, default in USER_FIELDS:
        if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": fieldname}):
            continue
        doc = {
            "doctype": "Custom Field",
            "dt": "User",
            "module": "Swift Theme",
            "fieldname": fieldname,
            "label": label,
            "fieldtype": fieldtype,
            "insert_after": insert_after,
        }
        if options is not None:
            doc["options"] = options
        if default is not None:
            doc["default"] = default
        frappe.get_doc(doc).insert(ignore_permissions=True)
        insert_after = fieldname


def _seed_settings():
    if not frappe.db.exists("DocType", "Swift Theme Settings"):
        return
    if not frappe.db.exists("Swift Theme Settings", "Swift Theme Settings"):
        frappe.get_doc({
            "doctype": "Swift Theme Settings",
            "default_accent": "indigo",
            "default_theme": "",
            "default_density": "Comfortable",
            "default_radius": "Rounded",
            "default_font_scale": "M",
            "default_font_family": "Inter",
            "navbar_variant": "Solid",
            "sidebar_variant": "Attached",
            "enable_switcher": 1,
            "enable_command_palette": 1,
            "enable_focus_mode": 1,
            "enable_perf_mode": 1,
            "enable_styled_scrollbar": 1,
            "enable_toast_theming": 1,
            "enable_print_theming": 1,
            "login_layout": "Split",
            "auto_dark_start": "19:00:00",
            "auto_dark_end": "07:00:00",
        }).insert(ignore_permissions=True)
