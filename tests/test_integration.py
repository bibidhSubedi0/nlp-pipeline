import json

from orchestrator.orchestrator import run_pipeline
from utils.envelope_factory import new_envelope

BENCHMARK_PATH = "data/benchmark_sentences.json"


def test_full_pipeline_on_clean_sentence():
    envelope = new_envelope("राम स्कूल जान्छ")
    result = run_pipeline(envelope)
    assert result["current_text"] != ""
    assert len(result["history"]) > 0
    assert all(
        step["status"] in ("success", "failed", "skipped")
        for step in result["history"]
    )


def test_full_pipeline_empty_input_does_not_crash():
    envelope = new_envelope("")
    result = run_pipeline(envelope)
    assert isinstance(result, dict)


def test_full_pipeline_whitespace_input_does_not_crash():
    envelope = new_envelope("   ")
    result = run_pipeline(envelope)
    assert isinstance(result, dict)


def test_benchmark_set_runs_without_exception():
    with open(BENCHMARK_PATH, encoding="utf-8") as f:
        cases = json.load(f)

    for case in cases:
        envelope = new_envelope(case["input"])
        result = run_pipeline(envelope)
        assert isinstance(result, dict), f"Failed on case {case['id']}: {case['note']}"
