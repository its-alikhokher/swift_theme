import frappe

from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
    PREMIUM_THEMES,
)


MODES = ["Follow Frappe", "Force Light", "Force Dark", "Auto (time-based)"]
DENSITIES = ["Compact", "Comfortable", "Cozy"]
RADII = ["Sharp", "Rounded", "Pill"]
FONT_SCALES = ["S", "M", "L", "XL"]
FONT_FAMILIES = ["Inter", "Poppins", "Manrope", "Roboto", "System"]
PRESETS = list(PREMIUM_THEMES.keys())

USER_FIELDS = [
    ("swift_follow_frappe", "Check",  "Follow Frappe's Theme Mode", None, "1"),
    ("swift_mode",          "Select", "Swift Mode Override",         "\n".join(MODES), "Follow Frappe"),
    ("swift_preset",        "Select", "Swift Theme Preset",          "\n".join([""] + PRESETS), ""),
    # A user may pick their own pair instead of a preset, straight from the
    # navbar theme switcher.
    ("swift_primary",       "Color",  "Swift Primary Color",         None, None),
    ("swift_secondary",     "Color",  "Swift Secondary Color",       None, None),
    ("swift_density",       "Select", "Swift Density",               "\n".join([""] + DENSITIES), ""),
    ("swift_radius",        "Select", "Swift Shape",                 "\n".join([""] + RADII), ""),
    ("swift_font_scale",    "Select", "Swift Font Scale",            "\n".join([""] + FONT_SCALES), ""),
    ("swift_font_family",   "Select", "Swift Font Family",           "\n".join([""] + FONT_FAMILIES), ""),
]

# Applied on install, and backfilled on migrate for rows still unset. These are
# the switches the desk JS gates on — leaving them NULL disables the switcher,
# command palette and focus mode outright.
SETTINGS_DEFAULTS = {
    "color_mode": "Theme Preset",
    "active_preset": "Iron Man",
    # Without these the Settings form shows Custom Mode and Colour Strength
    # blank, even though the code falls back to exactly these values.
    "custom_mode": "Dark",
    "custom_strength": "Subtle",
    "enable_backdrops": 1,
    "show_backdrop_through": 0,
    "default_density": "Comfortable",
    "default_radius": "Rounded",
    "default_font_scale": "M",
    "default_font_family": "Inter",
    "navbar_variant": "Solid",
    "sidebar_variant": "Floating",
    "pin_behavior": "Click to Pin",
    "enable_switcher": 1,
    "enable_command_palette": 1,
    "enable_focus_mode": 1,
    "enable_perf_mode": 1,
    "enable_styled_scrollbar": 1,
    "enable_toast_theming": 1,
    "enable_print_theming": 1,
    "print_font_family": "Inter",
    "login_layout": "Split",
    "enable_auto_dark": 0,
    "auto_dark_start": "19:00:00",
    "auto_dark_end": "07:00:00",
    "volume_level": 50,
}


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
        existing = frappe.db.get_value(
            "Custom Field", {"dt": "User", "fieldname": fieldname}, "name"
        )
        if existing:
            # Skipping outright was wrong: renaming the presets left
            # swift_preset holding the old option list for ever, so the new
            # presets were not selectable and apply_theme wrote a value the
            # Select rejected.
            if options is not None:
                field = frappe.get_doc("Custom Field", existing)
                if (field.options or "") != options:
                    field.options = options
                    field.save(ignore_permissions=True)
            insert_after = fieldname
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

    settings = frappe.get_single("Swift Theme Settings")

    # Only fill in what the admin hasn't set, so migrate never clobbers choices.
    changed = False
    for fieldname, value in SETTINGS_DEFAULTS.items():
        if not settings.meta.has_field(fieldname):
            continue
        if settings.get(fieldname) in (None, ""):
            settings.set(fieldname, value)
            changed = True

    changed = _repair_stale_selects(settings) or changed

    if changed:
        settings.flags.ignore_permissions = True
        settings.save(ignore_permissions=True)


def _repair_stale_selects(settings):
    """Reset Select fields holding a value the field no longer offers.

    A Select rejects a value outside its options on save, and this runs from
    after_migrate: one stale value — say an `active_preset` left behind because
    a rename patch didn't reach this site — raised ValidationError and took the
    whole seeding step down with it, so every genuinely new field stayed NULL.
    Repairing beats aborting: the site lands on a real default instead.
    """
    changed = False
    for fieldname, default in SETTINGS_DEFAULTS.items():
        field = settings.meta.get_field(fieldname)
        if not field or field.fieldtype != "Select":
            continue

        options = [o.strip() for o in (field.options or "").split("\n")]
        current = settings.get(fieldname)
        if current in (None, "") or current in options:
            continue

        frappe.log_error(
            title="Swift Theme: stale setting reset",
            message=f"{fieldname} held {current!r}, which is no longer an option. "
                    f"Reset to {default!r}.",
        )
        settings.set(fieldname, default)
        changed = True

    return changed
