from datetime import datetime, timezone

from utils.logger import get_logger
from utils.envelope_factory import new_envelope_safe

logger = get_logger("spellcheck")


def process(envelope: dict) -> dict:
    text = envelope["current_text"]

    if not text.strip():
        envelope["history"].append({
            "module": "spellcheck",
            "input": text,
            "output": text,
            "status": "skipped",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meta": {"reason": "empty input"},
        })
        return envelope

    output = text

    envelope["current_text"] = output
    envelope["history"].append({
        "module": "spellcheck",
        "input": text,
        "output": output,
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "meta": {},
    })
    return envelope
