import frappe

from swift_theme.settings_engine import adapter, boot, schema, validation


def extend_bootinfo(bootinfo):
    """Single boot path: canonical settings payload (backward compatible)."""
    bootinfo.swift_theme = boot.assemble()


@frappe.whitelist()
def get_effective_prefs():
    """Effective canonical settings for the current session."""
    return boot.assemble()


@frappe.whitelist()
def set_user_pref(field, value):
    """Save a single user preference. Whitelisted, validated subset only."""
    spec = schema.USER_FIELD_SPECS.get(field)
    if spec is None:
        frappe.throw("Field not allowed: {0}".format(field))

    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Login required")

    ok, message = validation.validate(spec, value)
    if not ok:
        frappe.throw("Invalid value for {0}: {1}".format(field, message))

    normalized = validation.normalize(spec, value)
    if normalized is None:
        frappe.throw("Invalid value for {0}".format(field))

    frappe.db.set_value("User", user, field, normalized)
    return {"ok": True, "field": field, "value": normalized}


def user_values():
    """Deprecation shim — use settings_engine.boot.user_values instead."""
    adapter.warn_deprecated("api.boot.user_values", usage="call")
    return boot.user_values()
