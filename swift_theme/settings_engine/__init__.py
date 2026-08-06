"""Swift Theme settings engine — single authoritative settings model.

All canonical settings access flows through this package:

- schema: the canonical + deprecated field registries (single source of truth)
- validation: centralized validation and sanitization (graceful rejection)
- migrate: idempotent, non-destructive v1 -> canonical migration
- adapter: canonical read/write regardless of underlying storage
- boot: single canonical boot payload (via ``extend_bootinfo`` only)

Public helpers: ``get`` / ``get_all`` / ``set`` / ``legacy`` read and write
canonical settings; ``run_migration`` runs the migration layer.
"""

from swift_theme.settings_engine import adapter, boot, migrate, schema, validation

__all__ = ["adapter", "boot", "migrate", "schema", "validation"]


def get(name):
    """Canonical value for a setting (validated, with default fallback)."""
    return adapter.get(name)


def get_all():
    """Flat dict of all canonical settings."""
    return adapter.get_all()


def set(name, value):
    """Validate + persist a canonical setting. Returns (ok, message)."""
    return adapter.set(name, value)


def legacy(name):
    """Read a deprecated (v1) field through the deprecation shim."""
    return adapter.legacy(name)


def validate_doc(doc):
    """Validate canonical fields of the Settings DocType (controller use)."""
    return validation.validate_doc(doc)


def schema_version():
    return adapter.schema_version()


def deprecated_fields():
    return adapter.deprecated()


def run_migration(verbose=False):
    """Run the full migration layer (idempotent). Alias of ``migrate.run``."""
    return migrate.run(verbose=verbose)


def assemble_boot():
    """Canonical boot payload for the current session."""
    return boot.assemble()
