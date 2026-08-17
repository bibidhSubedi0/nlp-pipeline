"""
Runtime pipeline configuration: which modules run, and in what order.

Two kinds of modules can be in the pipeline:

1. Native modules — Python files in modules/ with a process(envelope)
   function, referenced by dotted import path (e.g. "modules.normalizer").
2. Registry modules — extensions registered through a manifest (e.g.
   "sentiment-code"), referenced by their module_id.

The active pipeline is ONE ordered list that mixes both kinds. It lives in
pipeline_config.json (auto-created on first save). If the file is absent,
the default list (DEFAULT_CORE_MODULES) is used, so existing behaviour is
unchanged until someone saves a configuration.

The orchestrator reads ACTIVE_MODULES directly, so toggling modules at
runtime is just: config.pipeline_config.enable("my-module") / disable() /
move(). See PIPELINE_CONFIG.md for the full design.

Usage:
    from orchestrator.config import pipeline_config

    pipeline_config.enable("sentiment-code")     # add to the end
    pipeline_config.disable("modules.spellcheck")  # take out of the pipeline
    pipeline_config.move("modules.ner", "up")      # reorder
    pipeline_config.get_active_steps()             # ordered list of enabled ids
"""

import json
import os

_PIPELINE_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "pipeline_config.json")

# Default pipeline: the core modules, in their canonical order.
DEFAULT_CORE_MODULES = [
    "modules.normalizer",
    "modules.spellcheck",
    "modules.ner",
]

# Live ordered list of enabled steps. Native modules use dotted paths,
# registry modules use their module_id. The orchestrator reads this list
# directly, which is why the existing tests can still pin it in place.
ACTIVE_MODULES = list(DEFAULT_CORE_MODULES)


def is_native_step(step: str) -> bool:
    """A dotted path ('modules.ner') is a native import-path module;
    anything else is a registry module id ('sentiment-code')."""
    return "." in step


def step_label(step: str) -> str:
    """Short display name: 'modules.ner' -> 'ner', 'sentiment-code' stays."""
    return step.split(".")[-1] if is_native_step(step) else step


class PipelineConfig:
    """
    Persists the enabled step list to pipeline_config.json.
    All mutations apply to the module-level ACTIVE_MODULES list immediately
    and are written to disk, so a web save or CLI command takes effect for
    the next pipeline run with no restarts or code edits.
    """

    def __init__(self, path: str | None = None):
        self.path = path or _PIPELINE_CONFIG_PATH
        self.load()

    @property
    def file_exists(self) -> bool:
        return os.path.exists(self.path)

    def load(self) -> None:
        """Read the saved step list into ACTIVE_MODULES (no-op if absent)."""
        if not self.file_exists:
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return
        steps = data.get("steps", []) if isinstance(data, dict) else []
        ACTIVE_MODULES[:] = [s for s in steps if isinstance(s, str) and s]

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"steps": list(ACTIVE_MODULES)}, f, indent=2, ensure_ascii=False)

    def get_active_steps(self) -> list[str]:
        return list(ACTIVE_MODULES)

    def is_enabled(self, step: str) -> bool:
        return step in ACTIVE_MODULES

    def enable(self, step: str) -> bool:
        """Add a step to the end of the pipeline. Returns True if changed."""
        if step in ACTIVE_MODULES:
            return False
        ACTIVE_MODULES.append(step)
        self.save()
        return True

    def disable(self, step: str) -> bool:
        """Remove a step from the pipeline. Returns True if changed."""
        if step not in ACTIVE_MODULES:
            return False
        ACTIVE_MODULES.remove(step)
        self.save()
        return True

    def move(self, step: str, direction: str) -> bool:
        """Move a step 'up' or 'down' one position. Returns True if moved."""
        if step not in ACTIVE_MODULES or direction not in ("up", "down"):
            return False
        i = ACTIVE_MODULES.index(step)
        j = i - 1 if direction == "up" else i + 1
        if j < 0 or j >= len(ACTIVE_MODULES):
            return False
        ACTIVE_MODULES[i], ACTIVE_MODULES[j] = ACTIVE_MODULES[j], ACTIVE_MODULES[i]
        self.save()
        return True

    def set_steps(self, steps: list[str]) -> None:
        """Replace the whole pipeline with the given ordered list."""
        ACTIVE_MODULES[:] = [s for s in steps if isinstance(s, str) and s]
        self.save()


# Module-level singleton. Loads pipeline_config.json at import time, so the
# saved configuration is honoured everywhere (CLI, web, tests) immediately.
pipeline_config = PipelineConfig()
