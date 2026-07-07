"""
Dictionary + edit-distance spellchecker for Nepali (Devanagari) text.

Deliberately simple for a one-day-deadline demo: no ML model, no external
API — just a seed wordlist (data/ne_dictionary.txt) and Levenshtein distance
to suggest the closest known word for anything not found in the dictionary.

What it does:
- Tokenizes current_text into words (splits on whitespace, strips punctuation)
- Looks up each word in the dictionary (loaded once at import time)
- Unknown words get a suggestion = closest dictionary word within
  MAX_EDIT_DISTANCE, with a confidence score based on how close the match is
- current_text is NOT auto-corrected (too risky to silently rewrite a
  student's/user's input) — instead, findings are written to
  envelope["metadata"]["annotations"]["spellcheck"] and
  envelope["metadata"]["confidence_scores"]["spellcheck"], so a UI layer or
  a later module can decide what to do with them

What it deliberately does NOT do:
- Grammar checking (word order, agreement, conjugation correctness)
- Auto-rewrite current_text — this module only annotates, per Biprash's
  "modules pass through unchanged, errors/notes go in metadata" convention
"""

import os
import re

from utils.envelope_factory import now_iso

MODULE_NAME = "spellcheck"

_DICT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ne_dictionary.txt")
MAX_EDIT_DISTANCE = 2

# Devanagari letters/matras/digits only — excludes punctuation like
# । (U+0964) and ॥ (U+0965), which sit inside the same unicode block
# but aren't part of a word.
_WORD_RE = re.compile(r"[\u0900-\u0963\u0966-\u097F]+")


def _load_dictionary(path: str) -> set:
    words = set()
    if not os.path.exists(path):
        return words
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                words.add(line)
    return words


_DICTIONARY = _load_dictionary(_DICT_PATH)


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr_row = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr_row[j] = min(
                prev_row[j] + 1,      # deletion
                curr_row[j - 1] + 1,  # insertion
                prev_row[j - 1] + cost  # substitution
            )
        prev_row = curr_row
    return prev_row[-1]


def _closest_word(word: str, dictionary: set, max_distance: int):
    """Returns (suggestion, distance) or (None, None) if nothing close enough."""
    best_word = None
    best_dist = max_distance + 1
    for candidate in dictionary:
        # cheap length-based pre-filter before doing full edit distance
        if abs(len(candidate) - len(word)) > max_distance:
            continue
        dist = _levenshtein(word, candidate)
        if dist < best_dist:
            best_dist = dist
            best_word = candidate
            if dist == 0:
                break
    if best_word is None or best_dist > max_distance:
        return None, None
    return best_word, best_dist


def _check_text(text: str) -> dict:
    """Returns {"unknown_words": [...], "suggestions": {word: {...}}, "checked": n, "unknown": n}"""
    tokens = _WORD_RE.findall(text)
    unknown_words = []
    suggestions = {}

    for word in tokens:
        if word in _DICTIONARY:
            continue
        if word in suggestions:  # already processed this word once
            continue
        unknown_words.append(word)
        suggestion, distance = _closest_word(word, _DICTIONARY, MAX_EDIT_DISTANCE)
        if suggestion is not None:
            confidence = round(1 - (distance / max(len(word), 1)), 2)
            suggestions[word] = {
                "suggestion": suggestion,
                "edit_distance": distance,
                "confidence": max(confidence, 0.0)
            }
        else:
            suggestions[word] = {
                "suggestion": None,
                "edit_distance": None,
                "confidence": 0.0
            }

    return {
        "checked_words": len(tokens),
        "unknown_words": unknown_words,
        "suggestions": suggestions
    }


def process(envelope: dict) -> dict:
    input_text = envelope["current_text"]

    if not input_text:
        envelope["metadata"]["annotations"]["spellcheck"] = {
            "checked_words": 0,
            "unknown_words": [],
            "suggestions": {}
        }
        envelope["metadata"]["confidence_scores"]["spellcheck"] = 1.0
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
        result = _check_text(input_text)

        # Annotate only — do not rewrite current_text.
        envelope["metadata"]["annotations"]["spellcheck"] = {
            "checked_words": result["checked_words"],
            "unknown_words": result["unknown_words"],
            "suggestions": result["suggestions"]
        }

        # Overall confidence = fraction of words that were either known
        # or had a high-confidence suggestion.
        total = result["checked_words"]
        unknown = len(result["unknown_words"])
        overall_confidence = round((total - unknown) / total, 2) if total > 0 else 1.0
        envelope["metadata"]["confidence_scores"]["spellcheck"] = overall_confidence

        envelope["history"].append({
            "module": MODULE_NAME,
            "input": input_text,
            "output": input_text,  # unchanged — this module only annotates
            "status": "success",
            "timestamp": now_iso(),
            "meta": {
                "unknown_word_count": unknown,
                "checked_word_count": total
            }
        })
    except Exception as e:
        envelope["errors"].append({
            "module": MODULE_NAME,
            "error": str(e),
            "timestamp": now_iso()
        })
        # fail soft — current_text and metadata stay as they were

    return envelope
