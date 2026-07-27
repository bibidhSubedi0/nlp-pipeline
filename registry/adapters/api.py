"""
Adapter for 'api' provider_type.

Sends the full envelope (or a subset) to an HTTP endpoint and reads the
result back into the envelope's annotations.

The provider's manifest config must include:
    endpoint                    - URL to POST to
    method                      - HTTP method (default POST)
    headers                     - extra headers dict (default {})
    timeout                     - request timeout in seconds (default 30)
    response_annotations_field  - dot-path in response JSON for annotation data
    response_confidence_field   - dot-path in response JSON for confidence score

Request body sent to the endpoint:
    { "envelope": <full envelope> }

The adapter expects the response JSON to contain the annotation data at
the path specified by response_annotations_field.
"""

import requests

from registry.adapter import BaseAdapter
from utils.envelope_factory import now_iso
from utils.logger import get_logger

log = get_logger("adapter.api")


def _resolve_field(data: dict, dotpath: str):
    """Traverse a dict by dot-separated path, e.g. 'result.sentiment'."""
    keys = dotpath.split(".")
    for k in keys:
        if isinstance(data, dict) and k in data:
            data = data[k]
        else:
            return None
    return data


class APIAdapter(BaseAdapter):

    def load(self) -> None:
        cfg = self.manifest["config"]
        self._endpoint = cfg["endpoint"]
        self._method = cfg.get("method", "POST").upper()
        self._headers = cfg.get("headers", {})
        self._timeout = cfg.get("timeout", 30)
        self._ann_path = cfg.get("response_annotations_field", "sentiment")
        self._conf_path = cfg.get("response_confidence_field", "score")

        log.info("loaded api adapter: %s -> %s", self.module_id, self._endpoint)

    def process(self, envelope: dict) -> dict:
        input_text = envelope["current_text"]

        if not input_text or not input_text.strip():
            envelope["metadata"]["annotations"][self.annotations_key] = {
                "label": "neutral",
                "score": 0.0,
            }
            envelope["metadata"]["confidence_scores"][self.annotations_key] = 0.0
            envelope["history"].append({
                "module": self.module_id,
                "input": input_text,
                "output": input_text,
                "status": "skipped",
                "timestamp": now_iso(),
                "meta": {"reason": "empty input"},
            })
            return envelope

        try:
            payload = {"envelope": envelope}
            resp = requests.request(
                self._method,
                self._endpoint,
                json=payload,
                headers=self._headers,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            result = resp.json()

            annotation_data = _resolve_field(result, self._ann_path)
            confidence = _resolve_field(result, self._conf_path)

            if annotation_data is None:
                annotation_data = result

            envelope["metadata"]["annotations"][self.annotations_key] = (
                annotation_data if isinstance(annotation_data, dict) else {"value": annotation_data}
            )
            if confidence is not None:
                envelope["metadata"]["confidence_scores"][self.annotations_key] = round(
                    float(confidence), 4
                )

            envelope["history"].append({
                "module": self.module_id,
                "input": input_text,
                "output": input_text,
                "status": "success",
                "timestamp": now_iso(),
                "meta": {"endpoint": self._endpoint, "status_code": resp.status_code},
            })
        except requests.RequestException as e:
            envelope["errors"].append({
                "module": self.module_id,
                "error": f"API request failed: {e}",
                "timestamp": now_iso(),
            })
        except Exception as e:
            envelope["errors"].append({
                "module": self.module_id,
                "error": str(e),
                "timestamp": now_iso(),
            })

        return envelope
