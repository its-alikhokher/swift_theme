"""Rehearse the upgrade from the pre-release schema, then check the result.

The unit suite cannot cover this: `bench migrate` is a process, not a function,
and patches only run once per site. So this is two steps with a migrate between
them, and it is how the upgrade path is actually verified.

    bench --site your-site execute swift_theme.scripts.verify_upgrade.rewind
    bench --site your-site migrate
    bench --site your-site execute swift_theme.scripts.verify_upgrade.verify

`rewind` is destructive — it puts Swift Theme Settings back into the old shape
and clears this app's rows from the Patch Log. Run it on a scratch site.

Two bugs were found exactly here and nowhere else: a patch that saved the whole
document aborted the migrate on a stale `color_mode`, and seeding that raised on
a retired preset name left every new field NULL.
"""

import frappe

DOCTYPE = "Swift Theme Settings"

# A site as it looked before this work: old colour mode, old preset name, the
# gradient pair, and the fields that have since been retired.
OLD_STATE = {
    "color_mode": "Preset Themes",
    "active_preset": "Midnight Pro",
    "gradient_start": "#761ACB",
    "gradient_end": "#CB2929",
    "default_accent": "indigo",
    "default_theme": "",
    "brand_hex_override": "#123456",
    "volume_level": "50",
    "enable_switcher": "0",
    "enable_command_palette": "0",
}

OLD_USER_PRESET = "Emerald Luxury"


def rewind():
    """Put the site back into the pre-upgrade state."""
    # Delete before insert. tabSingles has no unique key on (doctype, field),
    # so an upsert silently leaves duplicate rows and every later read picks
    # whichever one comes back first.
    frappe.db.sql("delete from tabSingles where doctype = %s", DOCTYPE)
    for field, value in OLD_STATE.items():
        frappe.db.sql(
            "insert into tabSingles (doctype, field, value) values (%s, %s, %s)",
            (DOCTYPE, field, value),
        )

    frappe.db.set_value("User", "Administrator", "swift_preset", OLD_USER_PRESET)
    frappe.db.sql("delete from `tabPatch Log` where patch like %s", "%swift_theme%")
    frappe.db.commit()
    frappe.clear_cache()

    print(f"Rewound {frappe.local.site} to the pre-upgrade schema.")
    print("Now run: bench --site {} migrate".format(frappe.local.site))


def verify():
    """Check what the migrate actually did. Exits non-zero on any failure."""
    from swift_theme.api.boot import get_effective_prefs
    from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
        PREMIUM_THEMES,
    )

    rows = dict(
        frappe.db.sql("select field, value from tabSingles where doctype = %s", DOCTYPE)
        or []
    )
    prefs = get_effective_prefs()
    user_preset = frappe.db.get_value("User", "Administrator", "swift_preset")
    retired = ("default_accent", "default_theme", "brand_hex_override",
               "gradient_start", "gradient_end")
    counts = [r[0] for r in frappe.db.sql(
        "select count(*) from tabSingles where doctype = %s group by field", DOCTYPE)]

    checks = [
        ("colour mode converted",
         rows.get("color_mode") == "Theme Preset", rows.get("color_mode")),
        ("gradient became the brand pair",
         rows.get("primary_color") == OLD_STATE["gradient_start"]
         and rows.get("secondary_color") == OLD_STATE["gradient_end"],
         f"{rows.get('primary_color')} / {rows.get('secondary_color')}"),
        ("retired fields dropped",
         not any(f in rows for f in retired), "clean"),
        ("site preset renamed",
         rows.get("active_preset") == "Black Panther", rows.get("active_preset")),
        ("user preset renamed", user_preset == "Loki", user_preset),
        ("feature flags on",
         rows.get("enable_switcher") == "1"
         and rows.get("enable_command_palette") == "1", "switcher + palette"),
        ("new fields seeded",
         rows.get("custom_mode") == "Dark" and rows.get("custom_strength") == "Subtle",
         f"{rows.get('custom_mode')} / {rows.get('custom_strength')}"),
        ("desk resolves a live preset",
         prefs["preset_name"] in PREMIUM_THEMES, prefs["preset_name"]),
        ("stylesheet served",
         bool(prefs["theme_css"]), (prefs["theme_css"] or "").split("/")[-1]),
        ("backdrop resolved",
         prefs["backdrop"] in ("aurora", "mesh", "grain", "facets", "silk", "none"),
         prefs["backdrop"]),
        ("full role set delivered", len(prefs["roles"]) == 11, len(prefs["roles"])),
        ("no duplicated single rows", all(c == 1 for c in counts), "one row per field"),
    ]

    width = max(len(name) for name, _, _ in checks)
    print("\nUpgrade result:\n")
    for name, passed, detail in checks:
        print(f"  {name:<{width}}  {'PASS' if passed else 'FAIL'}   {detail}")

    failed = [name for name, passed, _ in checks if not passed]
    print(f"\n  {len(checks) - len(failed)}/{len(checks)} passed\n")

    if failed:
        frappe.throw("Upgrade verification failed: " + ", ".join(failed))
