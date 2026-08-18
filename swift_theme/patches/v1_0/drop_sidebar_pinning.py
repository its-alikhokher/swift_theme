"""Clear what sidebar pinning left behind.

Pinning put a star on every sidebar item, kept a list of pinned labels in the
browser, and reordered Frappe's own nav on each re-render. It was removed, so
the setting that configured it goes too — a Select nothing reads is worse than
no Select, because it still looks like a working control.

The per-browser pin list lives in localStorage and is not reachable from here;
it is simply never read again.
"""

import frappe

DOCTYPE = "Swift Theme Settings"
FIELD = "pin_behavior"


def execute():
    if not frappe.db.exists("DocType", DOCTYPE):
        return

    # Straight at the row: the field is gone from the DocType, so there is no
    # document API left that would reach it.
    frappe.db.sql(
        "delete from tabSingles where doctype = %s and field = %s", (DOCTYPE, FIELD)
    )

    frappe.db.sql(
        "delete from `tabProperty Setter` where doc_type = %s and field_name = %s",
        (DOCTYPE, FIELD),
    )

    frappe.clear_cache()
