"""
Loads the active pipeline steps from orchestrator/config.py, resolves each
one (native module by import path, extension by registry module_id), and
calls its process(envelope) function in order. Pure in-process function
calls — no network, no serialization between stages.

The pipeline is a single ordered list that mixes both kinds of modules:

    ["modules.normalizer", "modules.spellcheck", "modules.ner", "sentiment-code"]

Dotted entries are imported directly; bare ids are looked up in the module
registry and run through their adapter. Toggling a module in the pipeline
is done via orchestrator.config.pipeline_config (see PIPELINE_CONFIG.md).

Contract (per team-wide integration spec):
    run_pipeline(envelope: dict, steps: list[str] | None = None,
                 registry: Registry | None = None) -> dict

Callers build the envelope themselves via utils.envelope_factory.new_envelope
and pass it in — the orchestrator does not build envelopes, it only runs
modules against one.

Usage:
    from utils.envelope_factory import new_envelope
    from orchestrator.orchestrator import run_pipeline

    envelope = new_envelope("some raw nepali text")
    result = run_pipeline(envelope)
"""

import importlib

import orchestrator.config as config
from utils.validate_envelope import validate_envelope
from utils.logger import get_logger

log = get_logger(__name__)


def _resolve_step(step: str, registry=None):
    """
    Turn a step id into an object exposing process(envelope).
    Dotted ids are native modules (imported by path); bare ids are registry
    extensions (loaded through their adapter).
    """
    if config.is_native_step(step):
        return importlib.import_module(step)
    from registry.registry import Registry
    reg = registry if registry is not None else Registry()
    return reg.load(step)


def run_pipeline(envelope: dict, steps: list[str] | None = None,
                 registry=None) -> dict:
    original_input = envelope.get("original_input")
    step_list = list(steps) if steps is not None else config.ACTIVE_MODULES

    for step in step_list:
        try:
            module = _resolve_step(step, registry)
        except Exception as e:
            # Couldn't even load the step — record it and keep going.
            log.error("module %s not found or broken: %s", step, e)
            envelope["errors"].append({
                "module": step,
                "error": f"module '{step}' not found or broken: {e}",
            })
            envelope["original_input"] = original_input
            continue

        try:
            result = module.process(envelope)

            # Compatibility rule: modules must accept and return the exact
            # same envelope dict shape. If a module returns something else,
            # reject its output entirely rather than propagate a corrupted
            # envelope downstream.
            if not isinstance(result, dict):
                raise TypeError(
                    f"{step}.process() must return a dict, got {type(result).__name__}"
                )
            envelope = result
            validate_envelope(envelope)

            # Compatibility rule: original_input is read-only. If a module
            # mutated it, revert and log an error rather than letting the
            # rest of the pipeline see corrupted provenance.
            if envelope.get("original_input") != original_input:
                log.error("module %s mutated original_input; reverting", step)
                envelope["original_input"] = original_input
                envelope["errors"].append({
                    "module": step,
                    "error": "original_input mutated by module; reverted by orchestrator"
                })

            log.info("ran %s successfully", step)
        except Exception as e:
            # Fail soft: log the error into the envelope, keep going.
            # A bad module should not kill the whole pipeline run.
            log.error("module %s failed: %s", step, e)
            envelope["errors"].append({
                "module": step,
                "error": str(e),
            })
            # restore provenance in case the exception happened mid-mutation
            envelope["original_input"] = original_input

    return envelope


if __name__ == "__main__":
    import json
    from utils.envelope_factory import new_envelope

    envelope = new_envelope("नमस्ते, यो एक परीक्षण वाक्य हो।")
    result = run_pipeline(envelope)
    print(json.dumps(result, ensure_ascii=False, indent=2))
