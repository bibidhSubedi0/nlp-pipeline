"""
Shared helper to build a fresh, correctly-shaped envelope from raw input.
Nobody should hand-build envelope dicts — always use new_envelope().
"""

import uuid
from datetime import datetime, timezone


def new_envelope(input_text: str, language: str = "ne") -> dict:
    input_text = str(input_text)
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


def append_history(envelope: dict, module_name: str, status: str,
                   input_text: str, output_text: str, meta: dict | None = None) -> dict:
    """
    Append a history record and (for mutate-type modules) update current_text.
    Returns the same envelope for chaining. Every module should log its run
    through this helper so history entries are shaped identically.
    """
    envelope["history"].append({
        "module": module_name,
        "input": input_text,
        "output": output_text,
        "status": status,
        "timestamp": now_iso(),
        "meta": meta or {},
    })
    envelope["current_text"] = output_text
    return envelope


def append_error(envelope: dict, module_name: str, message: str) -> dict:
    """Append an error record to the envelope. Returns the same envelope."""
    envelope["errors"].append({
        "module": module_name,
        "error": message,
        "timestamp": now_iso(),
    })
    return envelope


def is_empty_input(envelope: dict) -> bool:
    """True if the current_text (not original_input) is empty or whitespace-only."""
    return not (envelope.get("current_text") or "").strip()
