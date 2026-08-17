"""
Backend logic for the web UI: runs text through the configured pipeline
(core stages + enabled extension modules, in one ordered list), and
auto-registers the built-in sentiment module on first use.

Also exposes helpers used by app.py to build the pipeline editor:
  - list_native_modules()       discover modules/*.py exposing process()
  - available_steps(registry)   all steps the user can enable/disable
"""

import importlib
import json
import os

from orchestrator.config import is_native_step, pipeline_config, step_label
from orchestrator.orchestrator import run_pipeline
from registry.registry import Registry
from utils.envelope_factory import new_envelope

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODULES_DIR = os.path.join(_ROOT, "modules")
_MANIFEST_DIR = os.path.join(_ROOT, "manifests")


def ensure_builtins(registry: Registry) -> None:
    """
    First-run bootstrap:
      1. Auto-register the built-in sentiment module if nothing is registered.
      2. If the pipeline config has never been saved, enable the built-in
         sentiment module so the demo behaves as before. Once the user saves
         a configuration, their choices win and nothing is auto-enabled.
    """
    if not registry.list_modules():
        manifest_path = os.path.join(_MANIFEST_DIR, "sentiment_code.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as f:
                try:
                    registry.register(json.load(f))
                except Exception:
                    pass

    if not pipeline_config.file_exists:
        if registry.get_manifest("sentiment-code") is not None:
            pipeline_config.enable("sentiment-code")


def list_native_modules() -> list[str]:
    """Dotted import paths of every modules/*.py that exposes process()."""
    found = []
    for filename in sorted(os.listdir(_MODULES_DIR)):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue
        stem = filename[:-3]
        try:
            mod = importlib.import_module(f"modules.{stem}")
        except Exception:
            continue
        if callable(getattr(mod, "process", None)):
            found.append(f"modules.{stem}")
    return found


def available_steps(registry: Registry) -> list[str]:
    """
    Every step the user can put in the pipeline:
      - native modules (modules/*.py), minus any already represented by a
        registered code-provider manifest (avoids duplicates for uploads)
      - registered extension module ids
    """
    registered_entry_points = {
        m.get("config", {}).get("entry_point")
        for m in registry.list_modules()
        if m.get("provider_type") == "code"
    }
    natives = [s for s in list_native_modules() if s not in registered_entry_points]
    extensions = [m["module_id"] for m in registry.list_modules()]
    return natives + extensions


def analyze(text: str, language: str = "ne", registry: Registry | None = None) -> dict:
    """
    Run the configured pipeline (native + enabled registry modules, in the
    saved order) on text. Disabled modules are simply not in the step list,
    so they never execute.
    """
    registry = registry or Registry()
    ensure_builtins(registry)

    envelope = new_envelope(text, language=language)
    return run_pipeline(envelope, registry=registry)


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
