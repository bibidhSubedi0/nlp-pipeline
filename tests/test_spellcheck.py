"""
Unit tests for modules/spellcheck.py

Run with: pytest tests/test_spellcheck.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.spellcheck import process
from utils.envelope_factory import new_envelope
from utils.validate_envelope import validate_envelope


def _run(text):
    envelope = new_envelope(text)
    result = process(envelope)
    validate_envelope(result)
    return result


def test_does_not_modify_current_text():
    result = _run("नमस्ते संसार")
    assert result["current_text"] == "नमस्ते संसार"


def test_all_known_words_gives_no_unknowns():
    result = _run("नमस्ते संसार")
    ann = result["metadata"]["annotations"]["spellcheck"]
    assert ann["unknown_words"] == []
    assert result["metadata"]["confidence_scores"]["spellcheck"] == 1.0


def test_flags_unknown_word():
    # "नमस्तेे" has an extra matra character -> not in dictionary
    result = _run("नमस्तेे संसार")
    ann = result["metadata"]["annotations"]["spellcheck"]
    assert len(ann["unknown_words"]) == 1


def test_suggests_close_match():
    # slight typo of नमस्ते
    result = _run("नमष्ते")
    ann = result["metadata"]["annotations"]["spellcheck"]
    unknown = ann["unknown_words"][0]
    suggestion = ann["suggestions"][unknown]["suggestion"]
    assert suggestion == "नमस्ते"


def test_history_records_unchanged_status():
    result = _run("नमस्ते")
    entry = result["history"][0]
    assert entry["module"] == "spellcheck"
    assert entry["input"] == entry["output"]  # never rewrites text


def test_empty_string_does_not_error():
    result = _run("")
    assert result["errors"] == []
    ann = result["metadata"]["annotations"]["spellcheck"]
    assert ann["checked_words"] == 0
    assert result["history"][-1]["status"] == "skipped"


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"PASS: {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
