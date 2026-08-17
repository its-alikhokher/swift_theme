"""Carry the old preset names over to the new ones.

The presets were renamed and re-tuned. `active_preset` and `User.swift_preset`
store the preset *name*, so without this every site and every user holding an
old name would resolve to nothing and silently drop to the default — including
sites that had deliberately chosen a theme.

Each old preset is mapped to whichever new one is closest in hue and mode, so
a site wakes up looking as close to its old self as the new set allows.
"""

import frappe

RENAMED = {
    # old name        -> new name       (why)
    "Swift Blue": "Captain America",     # light, blue
    "Midnight Pro": "Black Panther",     # dark, indigo/violet
    "Emerald Luxury": "Loki",            # dark, emerald
    "Rose Gold": "Scarlet Witch",        # light, rose
    "Sapphire Elite": "Winter Soldier",  # dark, blue
    "Golden Hour": "Vision",             # light, gold
    "Carbon Fiber": "Venom",             # dark, monochrome
    "Pearl White": "Captain America",    # light, cool neutral
    "Royal Purple": "Thanos",            # dark, purple
    "Ocean Depth": "Winter Soldier",     # dark, cyan/blue
    "Forest Mist": "Star-Lord",          # light, warm/green-adjacent
    "Crimson Red": "Hulk",               # dark — nearest remaining dark
}


def execute():
    if not frappe.db.exists("DocType", "Swift Theme Settings"):
        return

    current = frappe.db.get_single_value("Swift Theme Settings", "active_preset")
    if current in RENAMED:
        frappe.db.set_single_value(
            "Swift Theme Settings", "active_preset", RENAMED[current]
        )

    if frappe.db.has_column("User", "swift_preset"):
        for old, new in RENAMED.items():
            frappe.db.sql(
                """update `tabUser` set swift_preset = %s where swift_preset = %s""",
                (new, old),
            )

    frappe.clear_cache()
