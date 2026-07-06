from datetime import datetime, timezone

from utils.logger import get_logger

logger = get_logger("sentiment")


def process(envelope: dict) -> dict:
    text = envelope["current_text"]

    if not text.strip():
        envelope["history"].append({
            "module": "sentiment",
            "input": text,
            "output": text,
            "status": "skipped",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meta": {"reason": "empty input"},
        })
        return envelope

    output = text

    envelope["metadata"]["annotations"]["sentiment"] = {
        "label": "neutral",
        "score": 0.5,
    }
    envelope["history"].append({
        "module": "sentiment",
        "input": text,
        "output": output,
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "meta": {},
    })
    return envelope
