# Copyright (c) 2025, Swift Theme
# License: MIT

import frappe


def before_insert(doc, method):
    """Validate theme_key is URL-safe slug."""
    if doc.theme_key:
        import re
        if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', doc.theme_key):
            frappe.throw(
                "Theme Key must be a URL-safe slug: lowercase letters, digits and hyphens only."
            )


def before_save(doc, method):
    """Auto-generate theme_key from theme_name if not set."""
    if not doc.theme_key and doc.theme_name:
        import re
        slug = doc.theme_name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        doc.theme_key = slug.strip('-')
