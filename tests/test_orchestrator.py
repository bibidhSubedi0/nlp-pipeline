import sys
import types

from orchestrator.orchestrator import run_pipeline
from utils.envelope_factory import new_envelope


def test_orchestrator_runs_all_active_modules():
    envelope = new_envelope("राम स्कूल जान्छ")
    result = run_pipeline(envelope)
    ran_modules = [step["module"] for step in result["history"]]
    assert len(ran_modules) > 0, "Expected at least one module to run"


def test_orchestrator_skips_missing_module():
    from orchestrator import config
    original = list(config.ACTIVE_MODULES)
    try:
        config.ACTIVE_MODULES[:] = ["nonexistent_module"]
        envelope = new_envelope("test")
        result = run_pipeline(envelope)
        assert any("not found or broken" in e.get("error", "") for e in result["errors"])
    finally:
        config.ACTIVE_MODULES[:] = original


def test_orchestrator_continues_after_module_failure():
    def broken_process(envelope):
        raise ValueError("simulated failure")

    fake_module = types.SimpleNamespace(process=broken_process)
    from orchestrator import config
    original = list(config.ACTIVE_MODULES)
    try:
        config.ACTIVE_MODULES[:] = ["fake"]
        sys.modules["modules.fake"] = fake_module
        envelope = new_envelope("test")
        result = run_pipeline(envelope)
        assert len(result["errors"]) > 0, "Expected errors from module failure"
    finally:
        config.ACTIVE_MODULES[:] = original
        sys.modules.pop("modules.fake", None)
