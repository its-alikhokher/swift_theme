"""Idempotent, non-destructive migration from legacy (v1) to canonical settings.

Rules:
- idempotent      — rerunning produces no changes (fill-if-empty only)
- backward compat — legacy fields are never removed or overwritten
- non-destructive — a canonical value already set is never replaced
- safe to rerun   — every run recomputes the same delta; no-op once applied

The mapping logic (``apply_settings_migrations`` / ``apply_user_migration``)
is pure so it can be unit-tested without a bench.
"""

import frappe

from swift_theme.settings_engine import schema, validation

DOCTYPE = "Swift Theme Settings"


def _is_empty(spec, value):
    if spec.get("type") == "Check":
        return value is None
    return value is None or value == ""


def _normalize_sidebar(value):
    if value == "Minimal":
        return ("Icon-only", "sidebar_variant normalized Minimal -> Icon-only")
    if value in schema.SIDEBAR_VARIANTS:
        return (value, None)
    return (schema.CANONICAL_FIELDS["sidebar_variant"]["default"], "sidebar_variant reset to canonical default")


def apply_settings_migrations(values):
    """Pure: compute canonical updates from a dict of doc values.

    Args:
        values: mapping of field name -> stored value (v1 and/or canonical).

    Returns:
        (updates, notes): dict of canonical field -> value to set, and a list
        of human-readable notes describing what changed.
    """
    updates = {}
    notes = []

    # 1) Legacy premium preset -> canonical theme/accent (fill-if-empty).
    preset = values.get("active_preset")
    preset_map = schema.PRESET_MAP.get(preset) if isinstance(preset, str) else None
    if preset_map:
        for target, value in preset_map.items():
            spec = schema.get(target)
            if spec and _is_empty(spec, values.get(target)):
                updates[target] = value
                notes.append("migrated active_preset '{0}' -> {1}='{2}'".format(preset, target, value))

    # 2) Legacy gradient start -> brand hex override (fill-if-empty).
    gradient_start = values.get("gradient_start")
    target_spec = schema.get("brand_hex_override")
    if gradient_start and _is_empty(target_spec, values.get("brand_hex_override")):
        color = validation.normalize_color(gradient_start)
        if color:
            updates["brand_hex_override"] = color
            notes.append("migrated gradient_start -> brand_hex_override='{0}'".format(color))

    # 3) Sidebar variant: normalize legacy values into the canonical domain.
    current_sidebar = values.get("sidebar_variant")
    if isinstance(current_sidebar, str) and current_sidebar in ("Minimal",) or current_sidebar in schema.SIDEBAR_VARIANTS:
        normalized, note = _normalize_sidebar(current_sidebar)
        if note:
            updates["sidebar_variant"] = normalized
            notes.append(note)
    elif _is_empty(schema.CANONICAL_FIELDS["sidebar_variant"], current_sidebar):
        updates["sidebar_variant"] = schema.CANONICAL_FIELDS["sidebar_variant"]["default"]
        notes.append("sidebar_variant seeded with canonical default")

    # 4) Fill remaining empty canonical fields with schema defaults.
    # Only meaningful (non-empty) defaults are persisted; empty defaults are
    # resolved by the adapter at read time, so reruns stay no-op (idempotent).
    for name, spec in schema.canonical_specs().items():
        if name == "settings_schema_version":
            continue
        default = spec.get("default")
        if default is None or default == "":
            continue
        if _is_empty(spec, values.get(name)) and name not in updates:
            updates[name] = default

    # 5) Bump the schema version marker.
    current_version = validation.normalize_int(values.get("settings_schema_version"))
    if current_version is None or current_version < schema.SCHEMA_VERSION:
        updates["settings_schema_version"] = schema.SCHEMA_VERSION

    return updates, notes


def apply_user_migration(row):
    """Pure: migrate one User row's legacy ``swift_selected_theme``.

    Args:
        row: mapping with keys name / swift_selected_theme / swift_theme.

    Returns:
        (update_dict, note) — only fills ``swift_theme`` when empty.
    """
    legacy = row.get(schema.LEGACY_USER_FIELD)
    target = row.get(schema.LEGACY_USER_FIELD_TARGET)
    if legacy and not target:
        return {schema.LEGACY_USER_FIELD_TARGET: legacy}, (
            "migrated {0}.{1} -> {2}".format(row.get("name"), schema.LEGACY_USER_FIELD, schema.LEGACY_USER_FIELD_TARGET)
        )
    return {}, None


# ---------------------------------------------------------------------------
# Frappe-aware runners
# ---------------------------------------------------------------------------

def _get_settings_doc():
    try:
        return frappe.get_single(DOCTYPE)
    except Exception:
        return None


def migrate_settings(verbose=False):
    """Migrate the single Settings doc. Returns a summary dict."""
    doc = _get_settings_doc()
    if doc is None:
        return {"status": "skipped", "reason": "no settings doc", "changes": 0, "notes": []}

    values = {name: doc.get(name) for name in schema._ALL}
    updates, notes = apply_settings_migrations(values)
    if not updates:
        return {"status": "ok", "changes": 0, "notes": []}

    for name, value in updates.items():
        doc.set(name, value)
    doc.save(ignore_permissions=True)
    notes.append("schema version -> {0}".format(schema.SCHEMA_VERSION))
    return {"status": "migrated", "changes": len(updates), "notes": notes}


def migrate_user_prefs(verbose=False):
    """Migrate per-user legacy prefs. Returns a summary dict."""
    if not frappe.db.table_exists("User"):
        return {"status": "skipped", "reason": "no User table", "changes": 0, "notes": []}
    legacy = schema.LEGACY_USER_FIELD
    if not frappe.db.has_column("User", legacy):
        return {"status": "skipped", "reason": "no legacy column", "changes": 0, "notes": []}

    rows = frappe.db.get_all(
        "User",
        filters=[[legacy, "is", "set"]],
        fields=["name", legacy, schema.LEGACY_USER_FIELD_TARGET],
        limit_page_length=0,
    )
    changes = 0
    notes = []
    for row in rows:
        update, note = apply_user_migration(row)
        if update:
            frappe.db.set_value("User", row["name"], update, update_modified=False)
            changes += 1
            if note:
                notes.append(note)
    return {"status": "ok", "changes": changes, "notes": notes}


def run(verbose=False):
    """Run the full migration layer (idempotent)."""
    settings_result = migrate_settings(verbose=verbose)
    user_result = migrate_user_prefs(verbose=verbose)
    if verbose:
        for note in settings_result.get("notes", []):
            frappe.logger().info("[settings_engine:migrate] " + note)
        for note in user_result.get("notes", []):
            frappe.logger().info("[settings_engine:migrate] " + note)
    return {"settings": settings_result, "users": user_result}
