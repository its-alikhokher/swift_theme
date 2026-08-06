"""Centralized validation for canonical settings.

Pure functions (no frappe dependency) so they are unit-testable and usable
from both the DocType controller and the API layer. Invalid values are
rejected gracefully; ``sanitize`` returns a safe canonical value.
"""

import re

from swift_theme.settings_engine import schema

_HEX_COLOR = re.compile(r"^#?[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?(?:[0-9a-fA-F]{2})?(?:[0-9a-fA-F]{2})?$")
_TIME = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$")


def is_truthy(value):
    """Frappe Check truthiness (accepts 0/1/True/False/strings)."""
    return value in (1, True, "1", "true", "True", "on", "yes")


def normalize_check(value):
    if value is None or value == "":
        return None
    return 1 if is_truthy(value) else (0 if value in (0, False, "0", "false", "False", "off", "no") else None)


def normalize_int(value):
    if value is None or value == "":
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def normalize_text(value):
    if value is None:
        return None
    return str(value)


def normalize_time(value):
    if value is None or value == "":
        return None
    text = str(value).strip()
    if _TIME.match(text):
        return text
    # Frappe may store a full datetime for Time fields.
    if " " in text:
        candidate = text.split(" ")[1]
        if _TIME.match(candidate):
            return candidate
    return None


def normalize_color(value):
    if value is None or value == "":
        return None
    text = str(value).strip()
    if not _HEX_COLOR.match(text):
        return None
    if text.startswith("#"):
        return text
    return "#" + text


def normalize_select(value, options, optional):
    if value is None:
        return None
    text = str(value).strip()
    if optional and text == "":
        return ""
    return text if text in options else None


def normalize(spec, value):
    """Return a normalized canonical value, or None when invalid/unset."""
    ftype = spec.get("type")
    if ftype == "Check":
        return normalize_check(value)
    if ftype == "Int":
        return normalize_int(value)
    if ftype == "Select":
        return normalize_select(value, schema.options_of(spec), spec.get("optional", False))
    if ftype == "Color":
        return normalize_color(value)
    if ftype == "Time":
        return normalize_time(value)
    if ftype in ("Data", "Text"):
        return normalize_text(value)
    return value


def validate(spec, value):
    """Return (ok, message). None/empty for optional fields is accepted."""
    ftype = spec.get("type")
    optional = spec.get("optional", False)
    empty = value is None or value == ""

    if ftype == "Check":
        if normalize_check(value) is None:
            return False, "must be a boolean (0/1)"
        return True, ""
    if ftype == "Int":
        if empty and optional:
            return True, ""
        if normalize_int(value) is None:
            return False, "must be an integer"
        return True, ""
    if ftype == "Select":
        if empty and optional:
            return True, ""
        options = schema.options_of(spec)
        if normalize_select(value, options, optional) is None:
            return False, "must be one of: " + ", ".join(options)
        return True, ""
    if ftype == "Color":
        if empty and optional:
            return True, ""
        if normalize_color(value) is None:
            return False, "must be a hex color"
        return True, ""
    if ftype == "Time":
        if empty:
            return True, ""
        if normalize_time(value) is None:
            return False, "must be a valid time (HH:MM[:SS])"
        return True, ""
    if ftype in ("Data", "Text"):
        return True, ""
    return True, ""


def sanitize(spec, value, fallback=None):
    """Return a canonical value, falling back to spec default / caller default."""
    normalized = normalize(spec, value)
    if normalized is None:
        if fallback is not None:
            return fallback
        return spec.get("default")
    return normalized


def validate_many(values):
    """Validate a dict of {key: value}. Returns {key: error_message}."""
    errors = {}
    for key, value in values.items():
        spec = schema.get(key)
        if spec is None:
            errors[key] = "unknown setting"
            continue
        ok, message = validate(spec, value)
        if not ok:
            errors[key] = message
    return errors


def validate_doc(doc):
    """Validate canonical fields of a DocType object (controller use).

    Returns a list of human-readable "field: message" strings. Only
    canonical, non-system fields are checked; unset fields are fine.
    """
    errors = []
    for name, spec in schema.canonical_specs().items():
        if name == "settings_schema_version":
            continue
        if not hasattr(doc, "get") and not hasattr(doc, "getattr"):
            continue
        value = doc.get(name) if hasattr(doc, "get") else None
        if value is None or value == "":
            continue
        ok, message = validate(spec, value)
        if not ok:
            errors.append("{0}: {1}".format(name, message))
    return errors
