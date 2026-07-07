"""
TEMPLATE — only use this pattern if a module is genuinely a remote HTTP
service (e.g. another team's group only exposes a REST endpoint).
Don't build this speculatively — copy it only when you actually need it.

Still exposes process(envelope) -> envelope like every other module, so the
orchestrator doesn't need to know or care that this one goes over the network.
"""

import requests

from utils.envelope_factory import now_iso

MODULE_NAME = "external_service_name"  # rename to the actual service
SERVICE_URL = "http://<other-team-service>/process"  # fill in real URL


def process(envelope: dict) -> dict:
    input_text = envelope["current_text"]

    try:
        resp = requests.post(
            SERVICE_URL,
            json={"text": input_text},
            timeout=5  # never let one dead service hang the whole demo
        )
        resp.raise_for_status()
        result = resp.json()
        output_text = result["output_text"]

        envelope["current_text"] = output_text
        envelope["history"].append({
            "module": MODULE_NAME,
            "input": input_text,
            "output": output_text,
            "status": "success",
            "timestamp": now_iso(),
            "meta": {}
        })
    except (requests.RequestException, KeyError, ValueError) as e:
        envelope["errors"].append({
            "module": MODULE_NAME,
            "error": str(e),
            "timestamp": now_iso()
        })
        # envelope passed through unchanged — fail soft

    return envelope
