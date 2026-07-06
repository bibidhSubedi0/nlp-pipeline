"""
Central place to declare which modules are active and in what order.
Bibidh's orchestrator.py imports ACTIVE_MODULES from here — nobody hardcodes
the pipeline order inside orchestrator.py itself.

Each entry is a dotted import path to a module exposing:
    process(envelope: dict) -> dict

To enable/disable a stage for the demo, just comment/uncomment a line here.
Order matters — this is the order they'll run in.
"""

ACTIVE_MODULES = [
    "modules.normalizer",
    "modules.spellcheck",
    "modules.ner",
]
