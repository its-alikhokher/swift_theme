"""Fill in the login brand panel's text for sites that already existed.

Everything printed beside the sign-in form used to be written into the
template. It is Settings now, which is the point — but adding fields does not
backfill them. A Single that already has rows returns nothing for a field it
has never stored, and a Check comes back as 0, which _seed_settings treats as
a real answer rather than an unset one.

Without this, upgrading would blank the panel that was on the page yesterday:
the switch off, the heading, the description, the bullets and the figure all
empty. The values written here are the strings the template used to hold, so
an upgraded site looks exactly as it did, and now the text is editable.

Runs once. Anything the admin has already set is left alone.
"""

import frappe

DOCTYPE = "Swift Theme Settings"

COPY = {
    "login_show_brand_panel": 1,
    "login_heading": "Streamline Your\nBusiness Operations",
    "login_description": (
        "Unlock your ERP potential — build feature-rich dashboards, "
        "automate approvals and see every number in one place."
    ),
    "login_points": (
        "Role-based access control\n"
        "Encrypted sessions and audit trails\n"
        "Single sign-on ready"
    ),
    "login_stat_value": "300+",
    "login_stat_label": "implementations delivered. Be our next success story.",
}


def execute():
    if not frappe.db.exists("DocType", DOCTYPE):
        return

    meta = frappe.get_meta(DOCTYPE)
    for fieldname, value in COPY.items():
        if not meta.has_field(fieldname):
            continue

        # Only where nothing is stored. A site that has already written to one
        # of these — including deliberately clearing it — keeps what it chose.
        stored = frappe.db.exists("Singles", {"doctype": DOCTYPE, "field": fieldname})
        if stored:
            continue

        # Written straight to the row: a save would validate every other field
        # too, and this patch has no business failing over one of them.
        frappe.db.set_single_value(DOCTYPE, fieldname, value)

    frappe.clear_cache()
