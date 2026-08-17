"""
Integration tests for the full pipeline: normalizer -> spellcheck -> ner,
run through the real orchestrator (not individual module calls).

Contract: run_pipeline(envelope) — build the envelope yourself with
new_envelope(), pass it in, get the same dict back, mutated.

Run with: pytest tests/test_pipeline_integration.py -v
      or: python3 run_tests.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator.orchestrator import run_pipeline
from utils.envelope_factory import new_envelope
from utils.validate_envelope import validate_envelope


def test_full_pipeline_runs_without_errors():
    envelope = new_envelope("भीम काठमाडौं मा त्रिभुवन विश्वविद्यालय मा पढछ।")
    result = run_pipeline(envelope)
    assert result["errors"] == []


def test_full_pipeline_output_matches_schema():
    envelope = new_envelope("   राम   ,  श्याम   काठमाडौं जान्छन् ।")
    result = run_pipeline(envelope)
    validate_envelope(result)  # raises if shape is wrong


def test_all_three_stages_run_in_order():
    # The pipeline is runtime-configurable now, so pin it to the core
    # default for this exact-order assertion (a saved pipeline_config.json
    # must not change what this test expects).
    import orchestrator.config as config
    original = list(config.ACTIVE_MODULES)
    try:
        config.ACTIVE_MODULES[:] = config.DEFAULT_CORE_MODULES
        envelope = new_envelope("राम काठमाडौं जान्छ।")
        result = run_pipeline(envelope)
        modules_run = [entry["module"] for entry in result["history"]]
        assert modules_run == ["normalizer", "spellcheck", "ner"]
    finally:
        config.ACTIVE_MODULES[:] = original


def test_normalization_happens_before_downstream_stages_see_text():
    # messy whitespace/punctuation input -> by the time spellcheck/ner run,
    # they should be looking at the NORMALIZED text, not the raw input
    raw = "   राम    काठमाडौं   जान्छ  ।"
    envelope = new_envelope(raw)
    result = run_pipeline(envelope)

    normalizer_output = result["history"][0]["output"]
    spellcheck_input = result["history"][1]["input"]
    ner_input = result["history"][2]["input"]

    assert spellcheck_input == normalizer_output
    assert ner_input == normalizer_output
    assert normalizer_output != raw  # normalization actually did something


def test_ner_entities_reference_normalized_text_spans():
    # entity start/end offsets must be valid against current_text,
    # not against the messy original_input
    envelope = new_envelope("   राम काठमाडौं जान्छ ।")
    result = run_pipeline(envelope)
    current_text = result["current_text"]
    for entity in result["metadata"]["annotations"]["ner"]["entities"]:
        assert current_text[entity["start"]:entity["end"]] == entity["text"]


def test_pipeline_id_is_unique_per_run():
    result_a = run_pipeline(new_envelope("राम"))
    result_b = run_pipeline(new_envelope("राम"))
    assert result_a["pipeline_id"] != result_b["pipeline_id"]


def test_original_input_is_preserved_unmodified():
    raw = "   राम    काठमाडौं   जान्छ  ।"
    envelope = new_envelope(raw)
    result = run_pipeline(envelope)
    assert result["original_input"] == raw


def test_empty_input_does_not_crash_pipeline():
    envelope = new_envelope("")
    result = run_pipeline(envelope)
    assert result["errors"] == []
    assert result["current_text"] == ""
    assert all(step["status"] == "skipped" for step in result["history"])


def test_confidence_scores_present_for_active_annotation_modules():
    envelope = new_envelope("राम काठमाडौं जान्छ।")
    result = run_pipeline(envelope)
    scores = result["metadata"]["confidence_scores"]
    assert "spellcheck" in scores
    assert "ner" in scores


def test_disabling_a_module_in_config_is_respected():
    # sanity check that the orchestrator only runs what's in ACTIVE_MODULES,
    # not some hardcoded list -- guards against someone hardcoding stages
    # directly in orchestrator.py later.
    # Uses try/finally instead of a pytest fixture, per run_tests.py rules.
    import orchestrator.config as config
    original = list(config.ACTIVE_MODULES)
    try:
        config.ACTIVE_MODULES[:] = ["modules.normalizer"]
        envelope = new_envelope("राम   काठमाडौं")
        result = run_pipeline(envelope)
        modules_run = [entry["module"] for entry in result["history"]]
        assert modules_run == ["normalizer"]
        assert "ner" not in result["metadata"]["annotations"]
    finally:
        config.ACTIVE_MODULES[:] = original


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"PASS: {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
