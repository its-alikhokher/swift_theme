"""Remove the theme's own "Show Sign Up Link" switch.

It never worked. Frappe governs sign-up with `disable_signup` in Website
Settings, and this app ANDed its own checkbox with that — so with Frappe's
default in place, ticking it changed nothing, and the only way to find out was
to try. A control that looks live and is not is worse than no control.

The link it drew was broken too: it pointed at /signup, which is not a route.
Frappe puts sign-up on the login page itself, and this app replaces that page,
so the section had to be carried over rather than linked to.

Sign-up now appears exactly when Frappe would show it, from Frappe's own
setting, alongside the rest of what the stock login page offers.
"""

import frappe

DOCTYPE = "Swift Theme Settings"
FIELD = "login_show_signup"


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
