"""Schema registry invariants for the canonical settings model."""

import unittest

from swift_theme.settings_engine import schema


class TestSchemaInvariants(unittest.TestCase):
    def test_canonical_fields_are_complete(self):
        for name, spec in schema.canonical_specs().items():
            self.assertIn("type", spec, name)
            self.assertIn("default", spec, name)
            if spec.get("type") == "Select":
                self.assertTrue(spec.get("options"), name)
            self.assertIn("group", spec, name)

    def test_canonical_and_legacy_do_not_overlap(self):
        overlap = set(schema.canonical_specs()) & set(schema.legacy_specs())
        self.assertEqual(overlap, set())

    def test_every_field_is_addressable(self):
        for name in list(schema.canonical_specs()) + list(schema.legacy_specs()):
            self.assertIsNotNone(schema.get(name), name)

    def test_deprecation_markers(self):
        for name in schema.legacy_specs():
            self.assertTrue(schema.is_deprecated(name), name)
            self.assertFalse(schema.is_canonical(name), name)
        for name in schema.canonical_specs():
            self.assertFalse(schema.is_deprecated(name), name)
            self.assertTrue(schema.is_canonical(name), name)

    def test_legacy_mapping_targets_are_canonical(self):
        for name, spec in schema.legacy_specs().items():
            target = spec.get("maps_to")
            if target is not None:
                self.assertTrue(schema.is_canonical(target), "{0} -> {1}".format(name, target))

    def test_preset_map_targets_are_canonical(self):
        for preset, mapping in schema.PRESET_MAP.items():
            for target in mapping:
                self.assertTrue(schema.is_canonical(target), "{0} -> {1}".format(preset, target))

    def test_preset_map_values_valid(self):
        accents = set(schema.ACCENTS)
        themes = set(schema.THEMES)
        for preset, mapping in schema.PRESET_MAP.items():
            theme = mapping.get("default_theme")
            accent = mapping.get("default_accent")
            self.assertIn(theme, themes, preset)
            self.assertIn(accent, accents, preset)

    def test_user_field_specs_cover_install_fields(self):
        install_names = {entry[0] for entry in schema.USER_FIELDS}
        spec_names = set(schema.USER_FIELD_SPECS)
        self.assertEqual(install_names, spec_names)

    def test_sidebar_legacy_value_map(self):
        spec = schema.get("sidebar_variant")
        self.assertEqual(spec["legacy_value_map"]["Minimal"], "Icon-only")
        self.assertIn("Attached", schema.SIDEBAR_VARIANTS)
        self.assertIn("Floating", schema.SIDEBAR_VARIANTS)

    def test_schema_version_matches_marker_default(self):
        self.assertEqual(schema.SCHEMA_VERSION, 2)
        self.assertEqual(schema.defaults()["settings_schema_version"], schema.SCHEMA_VERSION)

    def test_options_of_adds_empty_for_optional(self):
        spec = schema.get("default_accent")
        options = schema.options_of(spec)
        self.assertEqual(options[0], "")
        self.assertIn("indigo", options)


if __name__ == "__main__":
    unittest.main()
