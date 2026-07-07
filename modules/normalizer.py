"""
Normalizes raw Nepali (Devanagari) text before it enters the rest of the
pipeline. This is usually the FIRST stage — spellcheck/NER etc. all assume
clean, consistently-formatted input.

What it does:
- Strips leading/trailing whitespace, collapses internal whitespace runs
- Normalizes Unicode to NFC (so visually-identical characters that are
  encoded differently — a common issue with Devanagari conjuncts and
  matras typed on different keyboards/IMEs — become byte-identical)
- Normalizes punctuation spacing (e.g. no space before ।, one space after)
- Removes zero-width characters (ZWJ/ZWNJ artifacts from some IMEs) that
  aren't intentionally used for conjunct control
- Collapses repeated punctuation (े.g. "??" -> "?")

What it deliberately does NOT do:
- Spellcheck or fix actual word-level errors (that's spellcheck.py's job)
- Change word choice, casing (Devanagari has no case), or meaning
"""

import re
import unicodedata

from utils.envelope_factory import now_iso

MODULE_NAME = "normalizer"

# Devanagari sentence-ending punctuation
_DANDA_CHARS = "।॥"

# Zero-width space/joiner/non-joiner that sometimes creep in from IMEs.
# We only strip the ones that aren't meaningfully joining/splitting
# conjuncts, i.e. runs of them or ones next to whitespace/punctuation.
_STRAY_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d]{2,}|(?<=\s)[\u200b\u200c\u200d]|[\u200b\u200c\u200d](?=\s)")

_WHITESPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([।॥,.!?])")
_REPEATED_PUNCT_RE = re.compile(r"([।॥!?])\1+")


def _normalize_text(text: str) -> str:
    # 1. Unicode normalization — NFC is the standard target form for Devanagari
    text = unicodedata.normalize("NFC", text)

    # 2. Strip stray zero-width characters
    text = _STRAY_ZERO_WIDTH_RE.sub("", text)

    # 3. Collapse horizontal whitespace runs, cap blank lines at 2
    text = _WHITESPACE_RE.sub(" ", text)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)

    # 4. No space before punctuation
    text = _SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)

    # 5. Collapse repeated punctuation (।। -> ।, ?? -> ?)
    text = _REPEATED_PUNCT_RE.sub(r"\1", text)

    # 6. Trim
    text = text.strip()

    return text


def process(envelope: dict) -> dict:
    input_text = envelope["current_text"]

    if not input_text:
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
        output_text = _normalize_text(input_text)

        envelope["current_text"] = output_text
        envelope["history"].append({
            "module": MODULE_NAME,
            "input": input_text,
            "output": output_text,
            "status": "success",
            "timestamp": now_iso(),
            "meta": {"changed": input_text != output_text}
        })
    except Exception as e:
        envelope["errors"].append({
            "module": MODULE_NAME,
            "error": str(e),
            "timestamp": now_iso()
        })
        # fail soft — current_text stays as it was

    return envelope
