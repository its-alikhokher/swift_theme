"""Remove the Custom CSS and Custom JS fields.

They let anyone with access to Swift Theme Settings inject arbitrary CSS and
JavaScript into every desk session on the site. That is a large amount of power
for a theming app to hold, it is not something a theme needs, and Frappe already
offers Client Scripts and a Website Script for people who genuinely want it —
behind their own permissions.

The fields are gone from the DocType, so the stored values are orphaned rows in
tabSingles. Deleting them means the code is not sitting in the database waiting
for a future field of the same name to pick it back up.
"""

import frappe

DOCTYPE = "Swift Theme Settings"
FIELDS = ("custom_css", "custom_js")


def execute():
    if not frappe.db.exists("DocType", DOCTYPE):
        return

    for field in FIELDS:
        # Straight at the row: the field no longer exists on the DocType, so
        # there is no document API left that would reach it.
        frappe.db.sql(
            "delete from tabSingles where doctype = %s and field = %s",
            (DOCTYPE, field),
        )
        frappe.db.sql(
            "delete from `tabProperty Setter` where doc_type = %s and field_name = %s",
            (DOCTYPE, field),
        )

    frappe.clear_cache()
