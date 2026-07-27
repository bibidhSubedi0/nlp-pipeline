"""
Built-in sentiment analyzer using keyword lexicons.

This is a 'code' provider_type module that works without any ML models,
API calls, or GPU. It uses hand-curated positive/negative word lists for
English and Nepali to produce a sentiment label and confidence score.

Designed as a working placeholder — swap this out for a HuggingFace or
API adapter when a real model is available.
"""

import re

from utils.envelope_factory import now_iso

MODULE_NAME = "sentiment_analyzer"

POSITIVE_EN = {
    "good", "great", "excellent", "amazing", "wonderful", "fantastic",
    "happy", "love", "best", "beautiful", "awesome", "perfect", "nice",
    "brilliant", "outstanding", "superb", "pleasant", "joy", "delight",
    "success", "win", "like", "enjoy", "fun", "exciting", "thanks",
    "thank", "grateful", "appreciate", "positive", "glad", "proud",
    "impressive", "remarkable", "magnificent", "terrific", "fabulous",
}

NEGATIVE_EN = {
    "bad", "terrible", "awful", "horrible", "worst", "hate", "ugly",
    "sad", "angry", "disgusting", "nasty", "poor", "fail", "failure",
    "wrong", "stupid", "boring", "annoying", "disappointing", "pain",
    "suffer", "problem", "error", "broken", "useless", "pathetic",
    "dreadful", "miserable", "unfortunate", "tragic", "loss", "lose",
    "fear", "worry", "stress", "difficult", "hard", "struggle", "complaint",
}

POSITIVE_NE = {
    "राम्रो", "ठीक", "सुन्दर", "माया", "खुसी", "रमाइलो", "उत्कृष्ट",
    "धन्यवाद", "शुभ", "सफल", "राम्रो", "भलो", "मीठो", "हर्ष", "आनन्द",
    "प्रसन्न", "प्रशंसा", "सम्मान", "जित", "लाभ", "सहज", "शान्त",
}

NEGATIVE_NE = {
    "नराम्रो", "खराब", "गन्द", "दुःख", "रिस", "गुस्सा", "समस्या",
    "गलत", "मूर्ख", "बेकार", "दुखद", "कष्ट", "हानि", "हार", "डर",
    "चिन्ता", "तनाव", "कठिन", "असफल", "निराश", "बिग्रिएको", "भ्रष्ट",
    "हिंसा", "आक्रमण", "दमन", "अत्याचार", "शोषण",
}

INTENSIFIERS = {"very", "extremely", "absolutely", "incredibly", "so", "really"}
NEGATORS = {"not", "no", "never", "neither", "nor", "don't", "doesn't",
            "didn't", "wasn't " "isn't", "aren't", "hardly", "barely",
            "नभए", "होइन", "कहिल्यै", "न", "नत्र"}

_WORD_RE = re.compile(r"[a-zA-Z\u0900-\u097F]+")


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


def _score_tokens(tokens: list[str]) -> tuple[float, int, int]:
    pos_count = 0
    neg_count = 0
    negated = False
    intensifier = 1.0

    for tok in tokens:
        if tok in NEGATORS:
            negated = True
            continue
        if tok in INTENSIFIERS:
            intensifier = 1.5
            continue

        hit = False
        if tok in POSITIVE_EN or tok in POSITIVE_NE:
            pos_count += 1
            hit = True
        elif tok in NEGATIVE_EN or tok in NEGATIVE_NE:
            neg_count += 1
            hit = True

        if hit and negated:
            pos_count, neg_count = neg_count, pos_count
            negated = False
        elif hit:
            negated = False

        if hit:
            intensifier = 1.0

    return pos_count * intensifier, neg_count * intensifier, len(tokens)


def analyze(text: str) -> dict:
    tokens = _tokenize(text)
    if not tokens:
        return {"label": "neutral", "score": 0.0}

    pos, neg, total = _score_tokens(tokens)
    raw = pos - neg
    magnitude = abs(raw)

    if raw > 0:
        label = "positive"
        score = min(0.5 + magnitude / (total + 1), 0.99)
    elif raw < 0:
        label = "negative"
        score = min(0.5 + magnitude / (total + 1), 0.99)
    else:
        label = "neutral"
        score = 0.5

    return {
        "label": label,
        "score": round(score, 4),
        "positive_hits": pos,
        "negative_hits": neg,
        "tokens_scored": total,
    }


def process(envelope: dict) -> dict:
    input_text = envelope["current_text"]

    if not input_text or not input_text.strip():
        envelope["metadata"]["annotations"]["sentiment"] = {
            "label": "neutral", "score": 0.0
        }
        envelope["metadata"]["confidence_scores"]["sentiment"] = 0.0
        envelope["history"].append({
            "module": MODULE_NAME,
            "input": input_text,
            "output": input_text,
            "status": "skipped",
            "timestamp": now_iso(),
            "meta": {"reason": "empty input"},
        })
        return envelope

    try:
        result = analyze(input_text)

        envelope["metadata"]["annotations"]["sentiment"] = result
        envelope["metadata"]["confidence_scores"]["sentiment"] = result["score"]

        envelope["history"].append({
            "module": MODULE_NAME,
            "input": input_text,
            "output": input_text,
            "status": "success",
            "timestamp": now_iso(),
            "meta": {"label": result["label"], "score": result["score"]},
        })
    except Exception as e:
        envelope["errors"].append({
            "module": MODULE_NAME,
            "error": str(e),
            "timestamp": now_iso(),
        })

    return envelope
