"""Compatibility adapter — canonical values regardless of underlying storage.

Every consumer (boot, API, future subsystems) reads settings through this
adapter, so no code ever needs to know whether a value originated from v1
or v2 storage. Legacy fields stay readable via ``legacy()`` and are marked
deprecated (dev-mode warnings only).
"""

import frappe

from swift_theme.settings_engine import schema, validation

DOCTYPE = "Swift Theme Settings"


def warn_deprecated(name, usage="read"):
    """Log a deprecation warning, only in developer mode."""
    if not (frappe.conf.get("developer_mode") or (frappe.local and frappe.local.conf and frappe.local.conf.get("developer_mode"))):
        return
    try:
        frappe.logger().warning(
            "[settings_engine] DEPRECATED field '{0}' ({1}) - remove usage".format(name, usage)
        )
    except Exception:
        pass


def _doc():
    try:
        return frappe.get_single(DOCTYPE)
    except Exception:
        return None


def get(name):
    """Canonical value for a setting, validated with fallback to default.

    Deprecated/unknown keys are not addressable through the canonical API.
    """
    spec = schema.get(name)
    if spec is None or schema.is_deprecated(name):
        warn_deprecated(name)
        return None
    doc = _doc()
    stored = doc.get(name) if doc is not None else None
    return validation.sanitize(spec, stored)


def get_all():
    """All canonical settings as a flat dict (validated canonical values)."""
    return {name: get(name) for name in schema.canonical_specs()}


def set(name, value):
    """Validate and persist a canonical setting.

    Returns (ok, message). Invalid or deprecated values are rejected
    gracefully (nothing written).
    """
    spec = schema.get(name)
    if spec is None:
        return False, "unknown setting: {0}".format(name)
    if schema.is_deprecated(name):
        warn_deprecated(name, usage="write")
        return False, "deprecated setting cannot be written through canonical API: {0}".format(name)

    ok, message = validation.validate(spec, value)
    if not ok:
        return False, "{0}: {1}".format(name, message)

    sanitized = validation.sanitize(spec, value)
    doc = _doc()
    if doc is None:
        return False, "settings document unavailable"
    try:
        doc.set(name, sanitized)
        doc.save(ignore_permissions=True)
    except Exception as exc:
        frappe.logger().error("[settings_engine] failed to set {0}: {1}".format(name, exc))
        return False, str(exc)
    return True, ""


def legacy(name):
    """Read a legacy (v1) field through the deprecation shim."""
    spec = schema.get(name)
    if spec is None or not schema.is_deprecated(name):
        return None
    warn_deprecated(name)
    doc = _doc()
    return doc.get(name) if doc is not None else None


def deprecated():
    """Names of deprecated (v1) fields still stored."""
    return sorted(schema.legacy_specs().keys())


def schema_version():
    return schema.SCHEMA_VERSION


def effective_user_pref(field, user_values, fallback):
    """Sanitized per-user preference value, falling back to ``fallback``.

    ``user_values`` is the raw row of User custom fields (dict). Invalid
    stored values are rejected gracefully (default/fallback used instead).
    """
    spec = schema.USER_FIELD_SPECS.get(field)
    if spec is None:
        return fallback
    return validation.sanitize(spec, user_values.get(field), fallback=fallback)
