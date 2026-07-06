"""
Unit tests for modules/ner.py

Run with: pytest tests/test_ner.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.ner import process
from utils.envelope_factory import new_envelope
from utils.validate_envelope import validate_envelope


def _run(text):
    envelope = new_envelope(text)
    result = process(envelope)
    validate_envelope(result)
    return result


def test_does_not_modify_current_text():
    result = _run("राम काठमाडौं जान्छ।")
    assert result["current_text"] == "राम काठमाडौं जान्छ।"


def test_finds_person_and_location():
    result = _run("राम काठमाडौं जान्छ।")
    ann = result["metadata"]["annotations"]["ner"]
    types = {e["type"] for e in ann["entities"]}
    assert "PERSON" in types
    assert "LOCATION" in types


def test_multiword_org_entity_matches():
    result = _run("भीम त्रिभुवन विश्वविद्यालय मा पढ्छ।")
    ann = result["metadata"]["annotations"]["ner"]
    org_matches = [e["text"] for e in ann["entities"] if e["type"] == "ORG"]
    assert "त्रिभुवन विश्वविद्यालय" in org_matches


def test_no_entities_gives_empty_list():
    result = _run("यो एक साधारण वाक्य हो।")
    ann = result["metadata"]["annotations"]["ner"]
    assert ann["entities"] == []
    assert result["metadata"]["confidence_scores"]["ner"] == 0.0


def test_entity_spans_are_correct():
    result = _run("राम")
    ann = result["metadata"]["annotations"]["ner"]
    entity = ann["entities"][0]
    assert entity["start"] == 0
    assert entity["end"] == 3
    assert entity["text"] == "राम"


def test_counts_by_type():
    result = _run("राम र श्याम काठमाडौं मा बस्छन्।")
    ann = result["metadata"]["annotations"]["ner"]
    assert ann["counts"].get("PERSON") == 2
    assert ann["counts"].get("LOCATION") == 1


def test_does_not_double_match_inside_multiword_entity():
    # "विश्वविद्यालय" alone isn't in the gazetteer, but ensure the
    # multi-word ORG match doesn't get split into overlapping partial hits
    result = _run("त्रिभुवन विश्वविद्यालय")
    ann = result["metadata"]["annotations"]["ner"]
    assert len(ann["entities"]) == 1
    assert ann["entities"][0]["type"] == "ORG"


def test_empty_string_does_not_error():
    result = _run("")
    assert result["errors"] == []
    ann = result["metadata"]["annotations"]["ner"]
    assert ann["entities"] == []
    assert result["history"][-1]["status"] == "skipped"


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"PASS: {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
