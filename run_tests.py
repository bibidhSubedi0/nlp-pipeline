"""
Run all tests without pytest.
Usage: python run_tests.py
"""

import sys
import traceback

sys.path.insert(0, ".")

modules = [
    ("test_orchestrator", "tests.test_orchestrator"),
    ("test_integration",  "tests.test_integration"),
]

exit_code = 0

for label, import_path in modules:
    try:
        __import__(import_path)
        mod = sys.modules[import_path]
    except Exception:
        print(f"[FAIL] {label} — failed to import")
        traceback.print_exc()
        exit_code = 1
        continue

    for name in dir(mod):
        if not name.startswith("test_"):
            continue
        fn = getattr(mod, name)
        if not callable(fn):
            continue
        try:
            fn()
            print(f"[PASS] {label}.{name}")
        except Exception:
            print(f"[FAIL] {label}.{name}")
            traceback.print_exc()
            exit_code = 1

sys.exit(exit_code)
