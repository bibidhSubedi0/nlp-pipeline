"""
Gazetteer-based Named Entity Recognizer for Nepali (Devanagari) text.

Deliberately simple for a one-day-deadline demo: no ML model (no NER
training data or GPU needed) — just a seed gazetteer
(data/ne_gazetteer.txt) of known PERSON / LOCATION / ORG surface forms,
matched against the text.

What it does:
- Loads the gazetteer once at import time (entries with underscores are
  treated as multi-word entities, e.g. "त्रिभुवन_विश्वविद्यालय" matches
  the phrase "त्रिभुवन विश्वविद्यालय" in running text)
- Scans current_text for gazetteer matches, longest-match-first so
  multi-word entities aren't shadowed by a shorter single-word match
  inside them
- Writes matches to envelope["metadata"]["annotations"]["ner"] as a list
  of {text, type, start, end} spans, plus a per-type count
- Does NOT modify current_text — annotation only, same convention as
  spellcheck.py

What it deliberately does NOT do:
- Statistical/contextual disambiguation (e.g. "राम" the name vs "राम" used
  generically) — a gazetteer hit is reported as-is; a real model would be
  needed to resolve ambiguity, which is out of scope for the seed version
- Coreference resolution across sentences
"""

import os
import re

from utils.envelope_factory import now_iso

MODULE_NAME = "ner"

_GAZETTEER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ne_gazetteer.txt")


def _load_gazetteer(path: str):
    """Returns list of (surface_form_with_spaces, entity_type), longest first."""
    entries = []
    if not os.path.exists(path):
        return entries
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            entity_type, surface = line.split("|", 1)
            surface = surface.replace("_", " ")
            entries.append((surface, entity_type))
    # Longest surface form first, so multi-word entities match before any
    # shorter entity that happens to be a substring of them.
    entries.sort(key=lambda pair: len(pair[0]), reverse=True)
    return entries


_GAZETTEER = _load_gazetteer(_GAZETTEER_PATH)


def _find_entities(text: str):
    """Returns list of {"text", "type", "start", "end"} spans, non-overlapping."""
    spans = []
    claimed = [False] * len(text)  # marks character positions already matched

    for surface, entity_type in _GAZETTEER:
        if not surface:
            continue
        for match in re.finditer(re.escape(surface), text):
            start, end = match.start(), match.end()
            if any(claimed[start:end]):
                continue  # overlaps an already-found (longer) entity
            spans.append({
                "text": text[start:end],
                "type": entity_type,
                "start": start,
                "end": end
            })
            for i in range(start, end):
                claimed[i] = True

    spans.sort(key=lambda s: s["start"])
    return spans


def process(envelope: dict) -> dict:
    input_text = envelope["current_text"]

    if not input_text:
        envelope["metadata"]["annotations"]["ner"] = {"entities": [], "counts": {}}
        envelope["metadata"]["confidence_scores"]["ner"] = 0.0
        envelope["history"].append({
            "module": MODULE_NAME,
            "input": input_text,
            "output": input_text,
            "status": "skipped",
            "timestamp": now_iso(),
            "meta": {"reason": "empty input"}
        })
        return envelope

    try:
        entities = _find_entities(input_text)

        counts = {}
        for entity in entities:
            counts[entity["type"]] = counts.get(entity["type"], 0) + 1

        envelope["metadata"]["annotations"]["ner"] = {
            "entities": entities,
            "counts": counts
        }

        # Simple confidence heuristic: gazetteer hits are exact-match, so
        # confidence is 1.0 per hit; overall score here just reflects that
        # entities were found at all vs. an empty result on non-trivial text.
        envelope["metadata"]["confidence_scores"]["ner"] = 1.0 if entities else 0.0

        envelope["history"].append({
            "module": MODULE_NAME,
            "input": input_text,
            "output": input_text,  # unchanged — annotation only
            "status": "success",
            "timestamp": now_iso(),
            "meta": {"entity_count": len(entities)}
        })
    except Exception as e:
        envelope["errors"].append({
            "module": MODULE_NAME,
            "error": str(e),
            "timestamp": now_iso()
        })
        # fail soft — current_text and metadata stay as they were

    return envelope
