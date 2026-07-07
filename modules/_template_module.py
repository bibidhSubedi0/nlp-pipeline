"""
TEMPLATE — copy this file to build a new module.

Every module MUST expose exactly one function:
    process(envelope: dict) -> dict

Rules:
- Read from envelope["current_text"], write your output back to
  envelope["current_text"].
- Append one entry to envelope["history"] describing what you did.
- Never raise on bad input — catch it and append to envelope["errors"]
  instead, then return the envelope unchanged (fail soft).
- Don't mutate envelope["original_input"].
"""

from utils.envelope_factory import now_iso

MODULE_NAME = "template_module"  # rename per module, e.g. "spellcheck"


def process(envelope: dict) -> dict:
    input_text = envelope["current_text"]

    try:
        # --- replace this block with real logic ---
        output_text = input_text
        # --------------------------------------------

        envelope["current_text"] = output_text
        envelope["history"].append({
            "module": MODULE_NAME,
            "input": input_text,
            "output": output_text,
            "status": "success",
            "timestamp": now_iso(),
            "meta": {}
        })
    except Exception as e:
        envelope["errors"].append({
            "module": MODULE_NAME,
            "error": str(e),
            "timestamp": now_iso()
        })
        # envelope["current_text"] stays as it was — fail soft

    return envelope
