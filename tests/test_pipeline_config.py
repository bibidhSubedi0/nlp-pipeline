"""
Tests for the runtime pipeline configuration: enabling/disabling/reordering
modules (native + registry extensions) and running the unified step list
through the orchestrator.

Rules per run_tests.py: zero-argument test functions, no pytest fixtures,
try/finally cleanup. Every test restores ACTIVE_MODULES and removes any
temp config files it creates.
"""

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator import config
from orchestrator.orchestrator import run_pipeline
from registry.registry import Registry
from utils.envelope_factory import new_envelope


def _reset():
    config.ACTIVE_MODULES[:] = config.DEFAULT_CORE_MODULES


def _temp_pipeline_config():
    tmpdir = tempfile.mkdtemp()
    return PipelineConfigInTmp(tmpdir), tmpdir


class PipelineConfigInTmp:
    """Small wrapper so each test gets an isolated config file."""

    def __init__(self, tmpdir):
        self.path = os.path.join(tmpdir, "pipeline_config.json")
        self.obj = config.PipelineConfig(self.path)


def _make_registry(tmpdir) -> Registry:
    """Isolated registry with a 'fake-ext' code module pointing at the
    real sentiment_analyzer, so it actually runs when enabled."""
    manifest = {
        "module_id": "fake-ext",
        "name": "Fake Extension",
        "version": "1.0.0",
        "provider_type": "code",
        "language": ["ne"],
        "behavior": "annotate",
        "annotations_key": "sentiment",
        "config": {"entry_point": "modules.sentiment_analyzer"},
    }
    reg = Registry(path=os.path.join(tmpdir, "modules.json"))
    reg.register(manifest)
    return reg


# ── PipelineConfig basics ───────────────────────────────────────────────────

def test_default_pipeline_is_core_modules_only():
    _reset()
    try:
        assert config.ACTIVE_MODULES == config.DEFAULT_CORE_MODULES
    finally:
        _reset()


def test_enable_appends_and_persists():
    _reset()
    pc, tmpdir = _temp_pipeline_config()
    try:
        pc.obj.enable("sentiment-code")
        assert pc.obj.get_active_steps() == config.DEFAULT_CORE_MODULES + ["sentiment-code"]
        assert pc.obj.is_enabled("sentiment-code")
        assert os.path.exists(pc.path)
        with open(pc.path, encoding="utf-8") as f:
            assert json.load(f)["steps"][-1] == "sentiment-code"
    finally:
        _reset()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_disable_removes_and_persists():
    _reset()
    pc, tmpdir = _temp_pipeline_config()
    try:
        pc.obj.enable("sentiment-code")
        pc.obj.disable("sentiment-code")
        assert "sentiment-code" not in pc.obj.get_active_steps()
        with open(pc.path, encoding="utf-8") as f:
            assert "sentiment-code" not in json.load(f)["steps"]
    finally:
        _reset()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_config_reloads_saved_steps():
    _reset()
    pc, tmpdir = _temp_pipeline_config()
    try:
        pc.obj.set_steps(["modules.ner", "sentiment-code", "modules.normalizer"])
        reloaded = config.PipelineConfig(pc.path)
        assert reloaded.get_active_steps() == ["modules.ner", "sentiment-code", "modules.normalizer"]
    finally:
        _reset()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_move_up_and_down_reorder():
    _reset()
    pc, tmpdir = _temp_pipeline_config()
    try:
        pc.obj.set_steps(["modules.normalizer", "modules.spellcheck", "modules.ner"])
        assert pc.obj.move("modules.ner", "up") is True
        assert pc.obj.get_active_steps() == ["modules.normalizer", "modules.ner", "modules.spellcheck"]
        assert pc.obj.move("modules.normalizer", "down") is True
        assert pc.obj.get_active_steps() == ["modules.ner", "modules.normalizer", "modules.spellcheck"]
        assert pc.obj.move("modules.ner", "up") is False  # already first
    finally:
        _reset()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_set_steps_replaces_whole_pipeline():
    _reset()
    pc, tmpdir = _temp_pipeline_config()
    try:
        pc.obj.set_steps(["modules.ner"])
        assert pc.obj.get_active_steps() == ["modules.ner"]
    finally:
        _reset()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_step_label_helpers():
    _reset()
    try:
        assert config.is_native_step("modules.ner") is True
        assert config.is_native_step("sentiment-code") is False
        assert config.step_label("modules.ner") == "ner"
        assert config.step_label("sentiment-code") == "sentiment-code"
    finally:
        _reset()


# ── Unified orchestration of native + registry steps ─────────────────────────

def test_orchestrator_runs_enabled_registry_module_after_natives():
    _reset()
    tmpdir = tempfile.mkdtemp()
    try:
        registry = _make_registry(tmpdir)
        pc = config.PipelineConfig(os.path.join(tmpdir, "pipeline_config.json"))
        pc.set_steps(config.DEFAULT_CORE_MODULES + ["fake-ext"])

        result = run_pipeline(new_envelope("This is an amazing day!"), registry=registry)
        modules_run = [step["module"] for step in result["history"]]
        assert modules_run == ["normalizer", "spellcheck", "ner", "sentiment_analyzer"]
        assert "sentiment" in result["metadata"]["annotations"]
    finally:
        _reset()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_orchestrator_skips_disabled_registry_module():
    _reset()
    tmpdir = tempfile.mkdtemp()
    try:
        registry = _make_registry(tmpdir)
        pc = config.PipelineConfig(os.path.join(tmpdir, "pipeline_config.json"))
        pc.set_steps(config.DEFAULT_CORE_MODULES)  # fake-ext NOT enabled

        result = run_pipeline(new_envelope("राम काठमाडौं जान्छ।"), registry=registry)
        modules_run = [step["module"] for step in result["history"]]
        assert modules_run == ["normalizer", "spellcheck", "ner"]
        assert "sentiment" not in result["metadata"]["annotations"]
    finally:
        _reset()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_orchestrator_reports_unknown_registry_step_and_continues():
    _reset()
    tmpdir = tempfile.mkdtemp()
    try:
        pc = config.PipelineConfig(os.path.join(tmpdir, "pipeline_config.json"))
        pc.set_steps(["modules.normalizer", "ghost-module"])

        result = run_pipeline(new_envelope("राम"))
        errors = [e for e in result["errors"] if e.get("module") == "ghost-module"]
        assert errors, "expected an error for the unknown registry step"
        assert "not found or broken" in errors[0]["error"]
        # the native step still ran afterwards
        assert any(step["module"] == "normalizer" for step in result["history"])
    finally:
        _reset()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_orchestrator_honours_explicit_steps_argument():
    _reset()
    try:
        result = run_pipeline(new_envelope("राम"), steps=["modules.ner"])
        modules_run = [step["module"] for step in result["history"]]
        assert modules_run == ["ner"]
    finally:
        _reset()


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"PASS: {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
