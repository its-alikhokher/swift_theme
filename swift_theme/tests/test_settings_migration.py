"""Migration layer: idempotent, non-destructive v1 -> canonical."""

import unittest

from swift_theme.settings_engine import migrate, schema, validation


def defaults():
    return dict(schema.defaults())


class TestSettingsMigration(unittest.TestCase):
    def test_v1_preset_maps_to_canonical(self):
        values = defaults()
        values.update({
            "active_preset": "Emerald Luxury",
            "gradient_start": "",
            "sidebar_variant": "Floating",
            "default_theme": None,
            "default_accent": None,
        })
        updates, notes = migrate.apply_settings_migrations(values)
        self.assertEqual(updates["default_theme"], "emerald")
        self.assertEqual(updates["default_accent"], "emerald")
        self.assertTrue(any("active_preset" in n for n in notes))

    def test_gradient_start_maps_to_brand_hex(self):
        values = defaults()
        values.update({"gradient_start": "#123456", "brand_hex_override": ""})
        updates, _ = migrate.apply_settings_migrations(values)
        self.assertEqual(updates["brand_hex_override"], "#123456")

    def test_canonical_value_never_overwritten(self):
        values = defaults()
        values["brand_hex_override"] = "#abcdef"
        values.update({"gradient_start": "#123456"})
        updates, _ = migrate.apply_settings_migrations(values)
        self.assertNotIn("brand_hex_override", updates)

    def test_sidebar_minimal_normalized_to_icon_only(self):
        values = defaults()
        values["sidebar_variant"] = "Minimal"
        updates, notes = migrate.apply_settings_migrations(values)
        self.assertEqual(updates["sidebar_variant"], "Icon-only")
        self.assertTrue(any("Icon-only" in n for n in notes))

    def test_empty_canonical_fields_filled_with_defaults(self):
        values = {name: None for name in schema.canonical_specs()}
        updates, _ = migrate.apply_settings_migrations(values)
        for name, spec in schema.canonical_specs().items():
            if name == "settings_schema_version":
                continue
            default = spec.get("default")
            if default is None or default == "":
                self.assertNotIn(name, updates, name)
            else:
                self.assertEqual(updates[name], default, name)

    def test_schema_version_bumped_from_v1(self):
        values = defaults()
        values["settings_schema_version"] = None
        updates, _ = migrate.apply_settings_migrations(values)
        self.assertEqual(updates["settings_schema_version"], schema.SCHEMA_VERSION)

    def test_idempotent_second_run_is_noop(self):
        values = defaults()
        values.update({
            "active_preset": "Emerald Luxury",
            "gradient_start": "#10b981",
            "sidebar_variant": "Minimal",
        })
        first, _ = migrate.apply_settings_migrations(values)
        applied = dict(values)
        applied.update(first)
        second, notes = migrate.apply_settings_migrations(applied)
        self.assertEqual(second, {})
        self.assertEqual(notes, [])

    def test_legacy_fields_never_removed(self):
        values = defaults()
        values.update({"active_preset": "Midnight Pro"})
        updates, _ = migrate.apply_settings_migrations(values)
        for legacy in schema.legacy_specs():
            self.assertNotIn(legacy, updates)


class TestUserMigration(unittest.TestCase):
    def test_legacy_user_pref_fills_empty_target(self):
        row = {"name": "user@x", "swift_selected_theme": "Midnight Pro", "swift_theme": ""}
        update, note = migrate.apply_user_migration(row)
        self.assertEqual(update, {"swift_theme": "Midnight Pro"})
        self.assertIsNotNone(note)

    def test_existing_target_not_overwritten(self):
        row = {"name": "user@x", "swift_selected_theme": "Midnight Pro", "swift_theme": "emerald"}
        update, _ = migrate.apply_user_migration(row)
        self.assertEqual(update, {})

    def test_no_legacy_value_is_noop(self):
        row = {"name": "user@x", "swift_selected_theme": "", "swift_theme": ""}
        update, _ = migrate.apply_user_migration(row)
        self.assertEqual(update, {})


if __name__ == "__main__":
    unittest.main()
