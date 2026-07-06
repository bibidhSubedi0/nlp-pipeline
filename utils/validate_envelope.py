REQUIRED_TOP_KEYS = {
    "pipeline_id", "original_input", "current_text", "encoding",
    "history", "metadata", "errors",
}
REQUIRED_METADATA_KEYS = {"language", "annotations", "confidence_scores"}
REQUIRED_HISTORY_KEYS = {"module", "input", "output", "status", "timestamp", "meta"}


def validate_envelope(envelope: dict) -> bool:
    missing_top = REQUIRED_TOP_KEYS - envelope.keys()
    if missing_top:
        raise ValueError(f"Envelope missing top-level keys: {missing_top}")

    meta = envelope.get("metadata", {})
    missing_meta = REQUIRED_METADATA_KEYS - meta.keys()
    if missing_meta:
        raise ValueError(f"Envelope metadata missing keys: {missing_meta}")

    for entry in envelope.get("history", []):
        missing_history = REQUIRED_HISTORY_KEYS - entry.keys()
        if missing_history:
            raise ValueError(f"History entry missing keys: {missing_history}")

    return True
