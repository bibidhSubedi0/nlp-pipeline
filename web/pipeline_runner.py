"""
Backend logic for the web UI: runs text through the core pipeline plus every
registered extension module, and auto-registers the built-in sentiment module
on first use (same behaviour as cli.py).
"""

import json
import os

from orchestrator.orchestrator import run_pipeline
from registry.registry import Registry
from utils.envelope_factory import new_envelope

_MANIFEST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "manifests")


def ensure_builtins(registry: Registry) -> None:
    """Auto-register the built-in sentiment module if nothing is registered."""
    if registry.list_modules():
        return
    manifest_path = os.path.join(_MANIFEST_DIR, "sentiment_code.json")
    if not os.path.exists(manifest_path):
        return
    with open(manifest_path, encoding="utf-8") as f:
        try:
            registry.register(json.load(f))
        except Exception:
            pass


def analyze(text: str, language: str = "ne", registry: Registry | None = None) -> dict:
    """Run the full pipeline (core stages + registered modules) on text."""
    registry = registry or Registry()
    ensure_builtins(registry)

    envelope = new_envelope(text, language=language)
    envelope = run_pipeline(envelope)

    for manifest in registry.list_modules():
        try:
            adapter = registry.load(manifest["module_id"])
            envelope = adapter.process(envelope)
        except Exception as e:
            envelope["errors"].append({
                "module": manifest["module_id"],
                "error": str(e),
            })

    return envelope


def highlight_entities(text: str, entities: list[dict]) -> list[dict]:
    """
    Splits text into segments of {text, type} where type is None for plain
    text and an entity type for matches. Non-overlapping, in document order.
    """
    segments = []
    cursor = 0
    for entity in sorted(entities, key=lambda e: e.get("start", 0)):
        start = entity.get("start", 0)
        end = entity.get("end", 0)
        if start < cursor or start >= len(text):
            continue
        if start > cursor:
            segments.append({"text": text[cursor:start], "type": None})
        segments.append({"text": text[start:end], "type": entity.get("type", "ENTITY")})
        cursor = max(cursor, end)
    if cursor < len(text):
        segments.append({"text": text[cursor:], "type": None})
    return segments