import uuid
from datetime import datetime, timezone


def new_envelope(text: str, language: str = "ne") -> dict:
    return {
        "pipeline_id": str(uuid.uuid4()),
        "original_input": text,
        "current_text": text,
        "encoding": "utf-8",
        "history": [],
        "metadata": {
            "language": language,
            "annotations": {},
            "confidence_scores": {},
        },
        "errors": [],
    }


def new_envelope_safe(text: str | None, language: str = "ne") -> dict:
    if text is None:
        text = ""
    text = text.strip()
    return new_envelope(text, language)
