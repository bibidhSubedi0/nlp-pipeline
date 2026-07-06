from datetime import datetime, timezone

from utils.logger import get_logger

logger = get_logger("normalizer")


def process(envelope: dict) -> dict:
    text = envelope["current_text"]

    if not text.strip():
        envelope["history"].append({
            "module": "normalizer",
            "input": text,
            "output": text,
            "status": "skipped",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meta": {"reason": "empty input"},
        })
        return envelope

    output = text.strip()

    envelope["current_text"] = output
    envelope["history"].append({
        "module": "normalizer",
        "input": text,
        "output": output,
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "meta": {},
    })
    return envelope
