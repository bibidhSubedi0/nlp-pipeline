"""
Biprash's integration tests: verify the envelope flows correctly between
modules through the real orchestrator.

Every test follows the required pattern:
    1. Create an envelope via utils.envelope_factory.new_envelope(text)
    2. Call orchestrator.orchestrator.run_pipeline(envelope)
    3. Assert on the result envelope shape

Run with: pytest tests/test_module_integration.py -v
      or: python3 run_tests.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.envelope_factory import new_envelope
from orchestrator.orchestrator import run_pipeline


def test_spellcheck_feeds_into_normalizer():
    envelope = new_envelope("राम स्कुल जान्छ")
    result = run_pipeline(envelope)

    # The envelope must survive every module
    assert isinstance(result, dict)
    assert "history" in result

    # Every module that ran must have recorded itself
    module_names = [step["module"] for step in result["history"]]
    assert "spellcheck" in module_names
    assert "normalizer" in module_names

    # No module should have crashed
    assert all(step["status"] != "failed" for step in result["history"])


def test_ner_receives_normalizer_and_spellcheck_output():
    envelope = new_envelope("राम   काठमाडौं   जान्छ")
    result = run_pipeline(envelope)

    module_names = [step["module"] for step in result["history"]]
    assert module_names == ["normalizer", "spellcheck", "ner"]
    assert all(step["status"] != "failed" for step in result["history"])


def test_envelope_required_keys_survive_full_pipeline():
    envelope = new_envelope("भीम त्रिभुवन विश्वविद्यालय मा पढ्छ।")
    result = run_pipeline(envelope)

    required_keys = [
        "pipeline_id", "original_input", "current_text",
        "encoding", "history", "metadata", "errors"
    ]
    for key in required_keys:
        assert key in result, f"missing required key: {key}"


def test_each_module_writes_its_own_annotation_key_only():
    envelope = new_envelope("राम काठमाडौं जान्छ।")
    result = run_pipeline(envelope)

    annotations = result["metadata"]["annotations"]
    # spellcheck and ner must each own exactly their key, not clobber
    # each other's output
    assert "spellcheck" in annotations
    assert "ner" in annotations
    assert annotations["spellcheck"] != annotations["ner"]


def test_no_module_returns_a_non_dict():
    # This is enforced by the orchestrator itself (TypeError -> caught ->
    # logged to errors), so a well-behaved pipeline run should never see
    # a "must return a dict" error in practice.
    envelope = new_envelope("राम")
    result = run_pipeline(envelope)
    for error in result["errors"]:
        assert "must return a dict" not in error.get("error", "")


def test_original_input_unchanged_across_full_run():
    raw = "   राम    काठमाडौं   जान्छ  ।"
    envelope = new_envelope(raw)
    result = run_pipeline(envelope)
    assert result["original_input"] == raw


def test_pipeline_does_not_crash_on_repeated_runs():
    # sanity check for state leaking between runs via module-level globals
    for text in ["राम", "श्याम", "काठमाडौं", ""]:
        envelope = new_envelope(text)
        result = run_pipeline(envelope)
        assert isinstance(result, dict)
        assert "history" in result


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"PASS: {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
