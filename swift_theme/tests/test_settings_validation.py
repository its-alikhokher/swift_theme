"""Centralized validation + sanitization of canonical settings."""

import unittest

from swift_theme.settings_engine import schema, validation


class TestValidation(unittest.TestCase):
    def test_check_normalize(self):
        self.assertEqual(validation.normalize_check("1"), 1)
        self.assertEqual(validation.normalize_check(0), 0)
        self.assertEqual(validation.normalize_check(True), 1)
        self.assertEqual(validation.normalize_check("no"), 0)
        self.assertIsNone(validation.normalize_check("bogus"))

    def test_select_accepts_valid_and_rejects_invalid(self):
        spec = schema.get("default_density")
        ok, _ = validation.validate(spec, "Compact")
        self.assertTrue(ok)
        ok, message = validation.validate(spec, "Bogus")
        self.assertFalse(ok)
        self.assertIn("Compact", message)

    def test_optional_select_accepts_empty(self):
        spec = schema.get("default_accent")
        ok, _ = validation.validate(spec, "")
        self.assertTrue(ok)
        ok, _ = validation.validate(spec, "indigo")
        self.assertTrue(ok)
        ok, _ = validation.validate(spec, "not-a-color")
        self.assertFalse(ok)

    def test_color_validation(self):
        spec = schema.get("brand_hex_override")
        ok, _ = validation.validate(spec, "#ff00ff")
        self.assertTrue(ok)
        ok, _ = validation.validate(spec, "ff00ff")
        self.assertTrue(ok)
        ok, _ = validation.validate(spec, "not a color")
        self.assertFalse(ok)
        self.assertEqual(validation.normalize_color("ff00ff"), "#ff00ff")

    def test_time_validation(self):
        spec = schema.get("auto_dark_start")
        ok, _ = validation.validate(spec, "19:00:00")
        self.assertTrue(ok)
        ok, _ = validation.validate(spec, "7:00")
        self.assertTrue(ok)
        ok, _ = validation.validate(spec, "25:99")
        self.assertFalse(ok)

    def test_int_validation(self):
        spec = schema.get("settings_schema_version")
        ok, _ = validation.validate(spec, 2)
        self.assertTrue(ok)
        ok, _ = validation.validate(spec, "abc")
        self.assertFalse(ok)

    def test_sanitize_falls_back_to_default(self):
        spec = schema.get("default_density")
        self.assertEqual(validation.sanitize(spec, "Bogus"), "Comfortable")
        self.assertEqual(validation.sanitize(spec, None), "Comfortable")
        self.assertEqual(validation.sanitize(spec, "Cozy"), "Cozy")

    def test_sanitize_respects_caller_fallback(self):
        spec = schema.get("default_accent")
        self.assertEqual(validation.sanitize(spec, "bogus", fallback="slate"), "slate")

    def test_validate_many_rejects_unknown(self):
        errors = validation.validate_many({"default_density": "Compact", "nope": 1})
        self.assertNotIn("default_density", errors)
        self.assertIn("nope", errors)

    def test_validate_doc_on_dict_like(self):
        class FakeDoc:
            def __init__(self, data):
                self._data = data

            def get(self, name):
                return self._data.get(name)

        doc = FakeDoc({"default_density": "Compact", "enable_switcher": 1, "default_accent": "indigo"})
        self.assertEqual(validation.validate_doc(doc), [])

        bad = FakeDoc({"default_density": "Bogus", "default_accent": "nope"})
        errors = validation.validate_doc(bad)
        self.assertEqual(len(errors), 2)


if __name__ == "__main__":
    unittest.main()
