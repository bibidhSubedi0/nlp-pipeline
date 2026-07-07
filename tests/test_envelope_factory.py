"""
tests/test_envelope_factory.py

Unit tests for utils/envelope_factory.py
Fully independent — no pipeline modules required.

Rules followed (per project spec):
  - Every test function takes zero arguments
  - No pytest fixtures or decorators
  - Each test is fully independent
  - All assertions are inline

Run with:
    python3 -m pytest tests/test_envelope_factory.py -v
    python3 run_tests.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.envelope_factory import (
    new_envelope,
    append_history,
    append_error,
    is_empty_input
)


# ── new_envelope: required keys ───────────────────────────────────────────────

def test_new_envelope_has_pipeline_id():
    env = new_envelope("राम स्कूल जान्छ")
    assert "pipeline_id" in env

def test_new_envelope_pipeline_id_is_string():
    env = new_envelope("राम स्कूल जान्छ")
    assert isinstance(env["pipeline_id"], str)

def test_new_envelope_pipeline_id_not_empty():
    env = new_envelope("राम स्कूल जान्छ")
    assert env["pipeline_id"] != ""

def test_new_envelope_has_original_input():
    env = new_envelope("राम स्कूल जान्छ")
    assert "original_input" in env

def test_new_envelope_has_current_text():
    env = new_envelope("राम स्कूल जान्छ")
    assert "current_text" in env

def test_new_envelope_has_encoding():
    env = new_envelope("राम स्कूल जान्छ")
    assert "encoding" in env

def test_new_envelope_has_history():
    env = new_envelope("राम स्कूल जान्छ")
    assert "history" in env

def test_new_envelope_has_metadata():
    env = new_envelope("राम स्कूल जान्छ")
    assert "metadata" in env

def test_new_envelope_has_errors():
    env = new_envelope("राम स्कूल जान्छ")
    assert "errors" in env


# ── new_envelope: field values ────────────────────────────────────────────────

def test_new_envelope_original_input_matches_text():
    env = new_envelope("राम स्कूल जान्छ")
    assert env["original_input"] == "राम स्कूल जान्छ"

def test_new_envelope_current_text_matches_text():
    env = new_envelope("राम स्कूल जान्छ")
    assert env["current_text"] == "राम स्कूल जान्छ"

def test_new_envelope_encoding_is_utf8():
    env = new_envelope("राम स्कूल जान्छ")
    assert env["encoding"] == "utf-8"

def test_new_envelope_history_starts_empty():
    env = new_envelope("राम स्कूल जान्छ")
    assert env["history"] == []

def test_new_envelope_errors_starts_empty():
    env = new_envelope("राम स्कूल जान्छ")
    assert env["errors"] == []


# ── new_envelope: metadata subkeys ───────────────────────────────────────────

def test_new_envelope_metadata_has_language():
    env = new_envelope("राम स्कूल जान्छ")
    assert "language" in env["metadata"]

def test_new_envelope_metadata_language_default_is_ne():
    env = new_envelope("राम स्कूल जान्छ")
    assert env["metadata"]["language"] == "ne"

def test_new_envelope_metadata_has_annotations():
    env = new_envelope("राम स्कूल जान्छ")
    assert "annotations" in env["metadata"]

def test_new_envelope_metadata_annotations_starts_empty():
    env = new_envelope("राम स्कूल जान्छ")
    assert env["metadata"]["annotations"] == {}

def test_new_envelope_metadata_has_confidence_scores():
    env = new_envelope("राम स्कूल जान्छ")
    assert "confidence_scores" in env["metadata"]

def test_new_envelope_metadata_confidence_scores_starts_empty():
    env = new_envelope("राम स्कूल जान्छ")
    assert env["metadata"]["confidence_scores"] == {}


# ── new_envelope: edge case inputs ────────────────────────────────────────────

def test_new_envelope_empty_string():
    env = new_envelope("")
    assert env["original_input"] == ""
    assert env["current_text"] == ""

def test_new_envelope_whitespace_only():
    env = new_envelope("   ")
    assert env["original_input"] == "   "
    assert env["current_text"] == "   "

def test_new_envelope_single_word():
    env = new_envelope("नमस्ते")
    assert env["current_text"] == "नमस्ते"

def test_new_envelope_non_string_coerced_to_string():
    env = new_envelope(123)
    assert isinstance(env["current_text"], str)

def test_new_envelope_mixed_script():
    env = new_envelope("म तीन बजे office जान्छु")
    assert env["current_text"] == "म तीन बजे office जान्छु"

def test_new_envelope_unicode_conjunct():
    env = new_envelope("क्ष")
    assert env["current_text"] == "क्ष"

def test_new_envelope_chandrabindu():
    env = new_envelope("सँगै")
    assert env["current_text"] == "सँगै"

def test_new_envelope_emoji():
    env = new_envelope("नमस्ते 😊")
    assert env["current_text"] == "नमस्ते 😊"

def test_new_envelope_original_input_never_mutated():
    """original_input must stay fixed even if a module changes current_text."""
    env = new_envelope("राम स्कूल जान्छ")
    env["current_text"] = "something else"
    assert env["original_input"] == "राम स्कूल जान्छ"

def test_new_envelope_each_call_gets_unique_pipeline_id():
    env1 = new_envelope("राम स्कूल जान्छ")
    env2 = new_envelope("राम स्कूल जान्छ")
    assert env1["pipeline_id"] != env2["pipeline_id"]


# ── append_history ────────────────────────────────────────────────────────────

def test_append_history_adds_one_record():
    env = new_envelope("राम स्कुल जान्छ")
    append_history(env, "spellcheck", "success",
                   "राम स्कुल जान्छ", "राम स्कूल जान्छ")
    assert len(env["history"]) == 1

def test_append_history_record_has_module():
    env = new_envelope("राम स्कुल जान्छ")
    append_history(env, "spellcheck", "success",
                   "राम स्कुल जान्छ", "राम स्कूल जान्छ")
    assert env["history"][0]["module"] == "spellcheck"

def test_append_history_record_has_status():
    env = new_envelope("राम स्कुल जान्छ")
    append_history(env, "spellcheck", "success",
                   "राम स्कुल जान्छ", "राम स्कूल जान्छ")
    assert env["history"][0]["status"] == "success"

def test_append_history_record_has_input():
    env = new_envelope("राम स्कुल जान्छ")
    append_history(env, "spellcheck", "success",
                   "राम स्कुल जान्छ", "राम स्कूल जान्छ")
    assert env["history"][0]["input"] == "राम स्कुल जान्छ"

def test_append_history_record_has_output():
    env = new_envelope("राम स्कुल जान्छ")
    append_history(env, "spellcheck", "success",
                   "राम स्कुल जान्छ", "राम स्कूल जान्छ")
    assert env["history"][0]["output"] == "राम स्कूल जान्छ"

def test_append_history_record_has_timestamp():
    env = new_envelope("राम स्कुल जान्छ")
    append_history(env, "spellcheck", "success",
                   "राम स्कुल जान्छ", "राम स्कूल जान्छ")
    assert "timestamp" in env["history"][0]

def test_append_history_record_has_meta():
    env = new_envelope("राम स्कुल जान्छ")
    append_history(env, "spellcheck", "success",
                   "राम स्कुल जान्छ", "राम स्कूल जान्छ")
    assert "meta" in env["history"][0]

def test_append_history_updates_current_text():
    env = new_envelope("राम स्कुल जान्छ")
    append_history(env, "spellcheck", "success",
                   "राम स्कुल जान्छ", "राम स्कूल जान्छ")
    assert env["current_text"] == "राम स्कूल जान्छ"

def test_append_history_multiple_records_stack():
    env = new_envelope("राम स्कुल जान्छ")
    append_history(env, "spellcheck", "success",
                   "राम स्कुल जान्छ", "राम स्कूल जान्छ")
    append_history(env, "normalizer", "success",
                   "राम स्कूल जान्छ", "राम स्कूल जान्छ")
    assert len(env["history"]) == 2

def test_append_history_status_failed():
    env = new_envelope("राम स्कुल जान्छ")
    append_history(env, "spellcheck", "failed",
                   "राम स्कुल जान्छ", "राम स्कुल जान्छ",
                   meta={"reason": "model not loaded"})
    assert env["history"][0]["status"] == "failed"

def test_append_history_status_skipped():
    env = new_envelope("")
    append_history(env, "spellcheck", "skipped", "", "",
                   meta={"reason": "empty input"})
    assert env["history"][0]["status"] == "skipped"

def test_append_history_returns_same_envelope():
    env = new_envelope("राम स्कूल जान्छ")
    result = append_history(env, "spellcheck", "success",
                            "राम स्कूल जान्छ", "राम स्कूल जान्छ")
    assert result is env


# ── append_error ──────────────────────────────────────────────────────────────

def test_append_error_adds_one_error():
    env = new_envelope("राम स्कूल जान्छ")
    append_error(env, "spellcheck", "model file not found")
    assert len(env["errors"]) == 1

def test_append_error_has_module_key():
    env = new_envelope("राम स्कूल जान्छ")
    append_error(env, "spellcheck", "model file not found")
    assert env["errors"][0]["module"] == "spellcheck"

def test_append_error_has_error_key():
    env = new_envelope("राम स्कूल जान्छ")
    append_error(env, "spellcheck", "model file not found")
    assert env["errors"][0]["error"] == "model file not found"

def test_append_error_multiple_errors_accumulate():
    env = new_envelope("राम स्कूल जान्छ")
    append_error(env, "spellcheck", "error one")
    append_error(env, "normalizer", "error two")
    assert len(env["errors"]) == 2

def test_append_error_returns_same_envelope():
    env = new_envelope("राम स्कूल जान्छ")
    result = append_error(env, "spellcheck", "something failed")
    assert result is env


# ── is_empty_input ────────────────────────────────────────────────────────────

def test_is_empty_input_true_for_empty_string():
    env = new_envelope("")
    assert is_empty_input(env) is True

def test_is_empty_input_true_for_whitespace_only():
    env = new_envelope("   ")
    assert is_empty_input(env) is True

def test_is_empty_input_false_for_normal_text():
    env = new_envelope("राम स्कूल जान्छ")
    assert is_empty_input(env) is False

def test_is_empty_input_false_for_single_word():
    env = new_envelope("नमस्ते")
    assert is_empty_input(env) is False

def test_is_empty_input_checks_current_text_not_original():
    """If a module clears current_text, is_empty_input must reflect that."""
    env = new_envelope("राम स्कूल जान्छ")
    env["current_text"] = ""
    assert is_empty_input(env) is True
