"""
tests/test_benchmark_loader.py

Unit tests for utils/benchmark_loader.py
Fully independent — no pipeline modules required.

Rules followed (per project spec):
  - Every test function takes zero arguments
  - No pytest fixtures or decorators
  - Each test is fully independent

Run with:
    python3 -m pytest tests/test_benchmark_loader.py -v
    python3 run_tests.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.benchmark_loader import load_all, load_inputs_only, summary


# ── load_all ──────────────────────────────────────────────────────────────────

def test_load_all_returns_list():
    assert isinstance(load_all(), list)

def test_load_all_not_empty():
    assert len(load_all()) > 0

def test_load_all_each_item_is_dict():
    for item in load_all():
        assert isinstance(item, dict)

def test_load_all_each_item_has_id():
    for item in load_all():
        assert "id" in item

def test_load_all_each_item_has_input():
    for item in load_all():
        assert "input" in item

def test_load_all_each_item_has_note():
    for item in load_all():
        assert "note" in item

def test_load_all_ids_are_unique():
    ids = [item["id"] for item in load_all()]
    assert len(ids) == len(set(ids))

def test_load_all_inputs_are_strings():
    for item in load_all():
        assert isinstance(item["input"], str), \
            f"id={item['id']} input is not a string"

def test_load_all_notes_are_strings():
    for item in load_all():
        assert isinstance(item["note"], str), \
            f"id={item['id']} note is not a string"

def test_load_all_ids_are_positive_integers():
    for item in load_all():
        assert isinstance(item["id"], int) and item["id"] > 0


# ── load_inputs_only ──────────────────────────────────────────────────────────

def test_load_inputs_only_returns_list():
    assert isinstance(load_inputs_only(), list)

def test_load_inputs_only_all_strings():
    for inp in load_inputs_only():
        assert isinstance(inp, str)

def test_load_inputs_only_count_matches_load_all():
    assert len(load_inputs_only()) == len(load_all())

def test_load_inputs_only_contains_empty_string():
    """Benchmark must include the empty string edge case."""
    assert "" in load_inputs_only()

def test_load_inputs_only_contains_whitespace_only():
    """Benchmark must include a whitespace-only edge case."""
    inputs = load_inputs_only()
    assert any(inp.strip() == "" and inp != "" for inp in inputs)

def test_load_inputs_only_contains_nepali_text():
    """Benchmark must have at least one actual Nepali sentence."""
    inputs = load_inputs_only()
    assert any(any('\u0900' <= c <= '\u097F' for c in inp) for inp in inputs)


# ── summary ───────────────────────────────────────────────────────────────────

def test_summary_returns_dict():
    assert isinstance(summary(), dict)

def test_summary_has_total_key():
    assert "total" in summary()

def test_summary_total_matches_load_all():
    assert summary()["total"] == len(load_all())

def test_summary_empty_string_count_is_positive():
    assert summary()["empty_string"] >= 1

def test_summary_whitespace_only_count_is_positive():
    assert summary()["whitespace_only"] >= 1
