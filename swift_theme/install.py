import frappe

from swift_theme.settings_engine import migrate, schema

FONT_SCALES = schema.FONT_SCALES
FONT_FAMILIES = schema.FONT_FAMILIES
DENSITIES = schema.DENSITIES
RADII = schema.RADII
MODES = schema.MODES
ACCENTS = schema.ACCENTS
THEMES = schema.THEMES

USER_FIELDS = schema.USER_FIELDS


def after_install():
    _ensure_user_fields()
    _seed_settings()
    migrate.run()
    frappe.db.commit()


def after_migrate():
    _ensure_user_fields()
    _seed_settings()
    migrate.run()
    frappe.db.commit()


def _ensure_user_fields():
    insert_after = "desk_theme"
    for fieldname, fieldtype, label, options, default in USER_FIELDS:
        if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": fieldname}):
            continue
        doc = {
            "doctype": "Custom Field",
            "dt": "User",
            "module": "Swift Theme",
            "fieldname": fieldname,
            "label": label,
            "fieldtype": fieldtype,
            "insert_after": insert_after,
        }
        if options is not None:
            doc["options"] = options
        if default is not None:
            doc["default"] = default
        frappe.get_doc(doc).insert(ignore_permissions=True)
        insert_after = fieldname


def _seed_settings():
    """Create the Settings doc from canonical schema defaults (idempotent)."""
    if not frappe.db.exists("DocType", "Swift Theme Settings"):
        return
    if not frappe.db.exists("Swift Theme Settings", "Swift Theme Settings"):
        doc = {"doctype": "Swift Theme Settings"}
        doc.update(schema.defaults())
        frappe.get_doc(doc).insert(ignore_permissions=True)
