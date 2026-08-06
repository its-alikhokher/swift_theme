import os
import sys
import types
import unittest


def _stub_frappe():
    if "frappe" in sys.modules:
        return
    stub = types.ModuleType("frappe")
    stub.session = types.SimpleNamespace(user="Administrator")
    stub.db = types.SimpleNamespace()
    stub.logger = lambda *a, **k: sys.stderr
    sys.modules["frappe"] = stub


def main():
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(tests_dir))
    sys.path.insert(0, repo_root)
    _stub_frappe()
    suite = unittest.defaultTestLoader.discover(
        tests_dir, pattern="test_settings_*.py"
    )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
