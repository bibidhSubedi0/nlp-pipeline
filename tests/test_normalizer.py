"""
Unit tests for modules/normalizer.py

Run with: pytest tests/test_normalizer.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.normalizer import process
from utils.envelope_factory import new_envelope
from utils.validate_envelope import validate_envelope


def _run(text):
    envelope = new_envelope(text)
    result = process(envelope)
    validate_envelope(result)  # should never fail the schema
    return result


def test_strips_leading_trailing_whitespace():
    result = _run("   नमस्ते   ")
    assert result["current_text"] == "नमस्ते"


def test_collapses_internal_whitespace():
    result = _run("यो    एक   परीक्षण   हो")
    assert result["current_text"] == "यो एक परीक्षण हो"


def test_no_space_before_danda():
    result = _run("यो एक परीक्षण वाक्य हो ।")
    assert result["current_text"] == "यो एक परीक्षण वाक्य हो।"


def test_collapses_repeated_punctuation():
    result = _run("के तपाईं ठीक हुनुहुन्छ??")
    assert result["current_text"] == "के तपाईं ठीक हुनुहुन्छ?"


def test_records_history_entry():
    result = _run("  नमस्ते  ")
    assert len(result["history"]) == 1
    assert result["history"][0]["module"] == "normalizer"
    assert result["history"][0]["status"] == "success"
    assert result["history"][0]["meta"]["changed"] is True


def test_no_change_when_already_clean():
    result = _run("नमस्ते संसार।")
    assert result["history"][0]["meta"]["changed"] is False


def test_never_raises_on_empty_string():
    result = _run("")
    assert result["current_text"] == ""
    assert result["errors"] == []
    assert result["history"][-1]["status"] == "skipped"


if __name__ == "__main__":
    # allow running without pytest installed, for a quick sanity check
    import inspect
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"PASS: {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
