"""Turn the backdrop feature on for sites that already existed.

`enable_backdrops` gates a feature that used to have no switch and was simply
always on. Adding the field does not backfill it: an existing Single row comes
back as 0, and _seed_settings deliberately only fills values that are None or
"" — 0 is a real answer for a Check, not an unset one. So without this every
upgrading site would quietly lose its backdrop and nothing would say why.

Runs once. Anyone who turns it off afterwards keeps it off, because the patch
log stops this from running again.

`show_backdrop_through` is left at 0 on purpose: that one is genuinely new
behaviour, so opting in is the right default.
"""

import frappe

FIELD = "enable_backdrops"


def execute():
    if not frappe.db.exists("DocType", "Swift Theme Settings"):
        return

    if not frappe.get_meta("Swift Theme Settings").has_field(FIELD):
        return

    # Written directly rather than through the document: a save validates every
    # other field too, and this patch has no business failing over one of them.
    frappe.db.set_single_value("Swift Theme Settings", FIELD, 1)
    frappe.clear_cache()
