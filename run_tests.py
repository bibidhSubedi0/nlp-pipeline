"""
Runs every test_*.py file in tests/ without needing pytest installed.

Discovers all functions starting with test_ in each tests/test_*.py module,
calls each with zero arguments, and reports pass/fail. Any test using
pytest-only features (fixtures like monkeypatch, tmpdir, parametrize) will
fail here even if it passes under pytest — that's intentional, it's the
compatibility check.

Usage:
    python3 run_tests.py
    python3 run_tests.py test_ner          # run only tests/test_ner.py
"""

import sys
import os
import importlib
import traceback

TESTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")


def discover_test_modules(filter_name=None):
    names = []
    for filename in sorted(os.listdir(TESTS_DIR)):
        if filename.startswith("test_") and filename.endswith(".py"):
            module_name = filename[:-3]
            if filter_name and filter_name not in module_name:
                continue
            names.append(module_name)
    return names


def run_all(filter_name=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    module_names = discover_test_modules(filter_name)
    if not module_names:
        print(f"No test modules found (filter={filter_name!r})")
        return 1

    total_passed = 0
    total_failed = 0
    failures = []

    for module_name in module_names:
        try:
            module = importlib.import_module(f"tests.{module_name}")
        except Exception as e:
            print(f"[ERROR] could not import tests.{module_name}: {e}")
            total_failed += 1
            failures.append((f"tests.{module_name}", "import", str(e)))
            continue

        test_fns = [
            (name, fn) for name, fn in vars(module).items()
            if name.startswith("test_") and callable(fn)
        ]

        if not test_fns:
            continue

        print(f"\n--- {module_name} ---")
        for name, fn in test_fns:
            try:
                fn()  # every test must be callable with zero arguments
                print(f"  PASS  {name}")
                total_passed += 1
            except Exception as e:
                print(f"  FAIL  {name}: {e}")
                traceback.print_exc(limit=1)
                total_failed += 1
                failures.append((module_name, name, str(e)))

    print(f"\n{'=' * 50}")
    print(f"{total_passed} passed, {total_failed} failed")

    if failures:
        print("\nFailures:")
        for mod, name, err in failures:
            print(f"  {mod}::{name} — {err}")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    filter_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(run_all(filter_arg))
