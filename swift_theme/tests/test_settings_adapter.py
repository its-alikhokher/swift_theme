"""Canonical adapter: values regardless of underlying storage."""

import unittest
from unittest import mock

from swift_theme.settings_engine import adapter, schema


class FakeDoc:
    def __init__(self, data):
        self._data = dict(data)

    def get(self, name):
        return self._data.get(name)

    def set_value(self, name, value):
        self._data[name] = value

    def save(self, ignore_permissions=False):
        pass


class TestAdapter(unittest.TestCase):
    def _patch(self, doc):
        frappe = mock.MagicMock()
        frappe.session.user = "Administrator"
        frappe.get_single.return_value = doc
        return mock.patch.object(adapter, "frappe", frappe)

    def test_get_returns_canonical_value(self):
        doc = FakeDoc({"default_density": "Cozy"})
        with self._patch(doc):
            self.assertEqual(adapter.get("default_density"), "Cozy")

    def test_get_falls_back_to_default_when_unset(self):
        doc = FakeDoc({})
        with self._patch(doc):
            self.assertEqual(adapter.get("default_density"), "Comfortable")
            self.assertEqual(adapter.get("default_accent"), "indigo")

    def test_get_returns_none_for_deprecated(self):
        doc = FakeDoc({"active_preset": "Midnight Pro"})
        with self._patch(doc):
            self.assertIsNone(adapter.get("active_preset"))

    def test_legacy_reads_deprecated_field(self):
        doc = FakeDoc({"active_preset": "Midnight Pro"})
        with self._patch(doc):
            self.assertEqual(adapter.legacy("active_preset"), "Midnight Pro")

    def test_set_rejects_invalid_value(self):
        doc = FakeDoc({"default_density": "Comfortable"})
        with self._patch(doc):
            ok, message = adapter.set("default_density", "Bogus")
            self.assertFalse(ok)
            self.assertIn("must be one of", message)
            self.assertEqual(doc.get("default_density"), "Comfortable")

    def test_set_rejects_deprecated(self):
        doc = FakeDoc({"active_preset": "Midnight Pro"})
        with self._patch(doc):
            ok, _ = adapter.set("active_preset", "Swift Blue")
            self.assertFalse(ok)

    def test_set_rejects_unknown(self):
        doc = FakeDoc({})
        with self._patch(doc):
            ok, _ = adapter.set("nope", 1)
            self.assertFalse(ok)

    def test_set_persists_valid_value(self):
        doc = FakeDoc({"default_density": "Comfortable"})
        with self._patch(doc):
            ok, _ = adapter.set("default_density", "Cozy")
            self.assertTrue(ok)
            self.assertEqual(doc.get("default_density"), "Cozy")
            adapter.frappe.get_single.assert_called()

    def test_get_all_returns_only_canonical(self):
        doc = FakeDoc({})
        with self._patch(doc):
            all_values = adapter.get_all()
            self.assertEqual(
                set(all_values), set(schema.canonical_specs())
            )

    def test_deprecated_lists_legacy_fields(self):
        self.assertEqual(set(adapter.deprecated()), set(schema.legacy_specs()))


if __name__ == "__main__":
    unittest.main()
