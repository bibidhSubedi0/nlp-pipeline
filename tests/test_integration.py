"""
Runs every sentence in data/benchmark_sentences.json through the full
pipeline and asserts nothing crashes and every envelope is schema-valid.

If Bibek appends new entries to benchmark_sentences.json, this test picks
them up automatically — no code change needed here.

Run with: pytest tests/test_integration.py -v
      or: python3 run_tests.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator.orchestrator import run_pipeline
from utils.envelope_factory import new_envelope
from utils.validate_envelope import validate_envelope

_BENCHMARK_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "benchmark_sentences.json")


def _load_benchmark_set():
    with open(_BENCHMARK_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_benchmark_set_runs_without_exception():
    sentences = _load_benchmark_set()
    assert len(sentences) > 0, "benchmark_sentences.json should not be empty"

    for entry in sentences:
        envelope = new_envelope(entry["input"])
        result = run_pipeline(envelope)
        validate_envelope(result)  # raises on shape violations
        assert result["errors"] == [], (
            f"entry id={entry['id']} ({entry['note']}) produced errors: {result['errors']}"
        )


def test_benchmark_ids_are_unique():
    sentences = _load_benchmark_set()
    ids = [entry["id"] for entry in sentences]
    assert len(ids) == len(set(ids)), "duplicate id found in benchmark_sentences.json"


def test_benchmark_entries_have_required_fields():
    sentences = _load_benchmark_set()
    for entry in sentences:
        assert "id" in entry
        assert "input" in entry
        assert "note" in entry
        assert isinstance(entry["input"], str)


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"PASS: {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
