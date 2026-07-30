# Copyright (c) 2025, Swift Theme
# License: MIT

import frappe


def before_save(doc, method):
    """Validate sound mappings."""
    if doc.sounds:
        for row in doc.sounds:
            if row.event_key and not row.file:
                frappe.throw(f"Audio file required for event: {row.event_key}")
