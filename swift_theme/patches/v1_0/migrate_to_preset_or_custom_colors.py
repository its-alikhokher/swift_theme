"""Collapse the colour settings into "Theme Preset" or "Custom Colors".

Swift Theme used to carry three overlapping colour controls: a single accent
(default_accent), a separate full-theme picker (default_theme), a brand hex
override, and a gradient pair. They were partly duplicated and partly dead.

This moves whatever the site had onto the new two-way model, without losing a
configured gradient.
"""

import frappe

COLOR_MODE_MAP = {
    "Preset Themes": "Theme Preset",
    "Custom Gradient": "Custom Colors",
}


def execute():
    if not frappe.db.exists("DocType", "Swift Theme Settings"):
        return

    stored = dict(
        frappe.db.sql(
            """select field, value from tabSingles where doctype = 'Swift Theme Settings'"""
        )
        or []
    )
    if not stored:
        return

    updates = {}

    # The gradient pair becomes the brand pair.
    if stored.get("gradient_start") and not stored.get("primary_color"):
        updates["primary_color"] = stored["gradient_start"]
    if stored.get("gradient_end") and not stored.get("secondary_color"):
        updates["secondary_color"] = stored["gradient_end"]

    # A brand override was the closest thing to a primary colour.
    if stored.get("brand_hex_override") and not updates.get("primary_color"):
        updates["primary_color"] = stored["brand_hex_override"]

    new_mode = COLOR_MODE_MAP.get(stored.get("color_mode"))
    if new_mode:
        updates["color_mode"] = new_mode

    if (updates.get("color_mode") or stored.get("color_mode")) == "Custom Colors":
        # Custom Colors needs both halves; fall back rather than leave it invalid.
        updates.setdefault("primary_color", stored.get("gradient_start") or "#0b84f3")
        updates.setdefault("secondary_color", stored.get("gradient_end") or "#0056b3")

    # active_preset is deliberately left alone when empty. This patch used to
    # write "Swift Blue", a preset that no longer exists — it only ever
    # resolved because the later rename patch happened to map it. install's
    # _seed_settings runs after every migrate and fills an empty value with
    # whatever the current default is, which cannot go stale.

    for field, value in updates.items():
        frappe.db.set_single_value("Swift Theme Settings", field, value)

    # Retire the columns this patch replaces.
    for dead in ("default_accent", "default_theme", "brand_hex_override",
                 "gradient_start", "gradient_end"):
        frappe.db.sql(
            """delete from tabSingles where doctype = 'Swift Theme Settings' and field = %s""",
            dead,
        )

    # The per-user accent/full-theme fields no longer have anything behind them.
    for fieldname in ("swift_accent", "swift_theme"):
        name = frappe.db.get_value("Custom Field", {"dt": "User", "fieldname": fieldname})
        if name:
            frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)

    frappe.clear_cache()
