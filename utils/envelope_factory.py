"""
Shared helper to build a fresh, correctly-shaped envelope from raw input.
Nobody should hand-build envelope dicts — always use new_envelope().
"""

import uuid
from datetime import datetime, timezone


def new_envelope(input_text: str, language: str = "ne") -> dict:
    return {
        "pipeline_id": str(uuid.uuid4()),
        "original_input": input_text,
        "current_text": input_text,
        "encoding": "utf-8",
        "history": [],
        "metadata": {"language": language, "annotations": {}, "confidence_scores": {}},
        "errors": []
    }


def now_iso() -> str:
    """Shared timestamp helper so every module logs history entries the same way."""
    return datetime.now(timezone.utc).isoformat()
