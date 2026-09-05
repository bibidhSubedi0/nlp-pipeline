"""
Adapter for 'huggingface' provider_type.

Uses the HuggingFace `transformers` pipeline API to load a model and run
inference. Wraps the result into the envelope's annotation format.

Requirements:
    pip install transformers torch

The provider's manifest config must include:
    model       - HuggingFace model ID (e.g. "cardiffnlp/twitter-xlm-roberta-base-sentiment")
    task        - pipeline task (default: "text-classification")
    device      - "cpu", "cuda", or "auto" (default: "cpu")
    max_length  - max token length (default: 512)
"""

from registry.adapter import BaseAdapter
from utils.envelope_factory import now_iso
from utils.logger import get_logger

log = get_logger("adapter.huggingface")


class HuggingFaceAdapter(BaseAdapter):

    def load(self) -> None:
        try:
            from transformers import pipeline as hf_pipeline
        except ImportError:
            raise ImportError(
                f"Module '{self.module_id}' requires the 'transformers' package. "
                "Install it with: pip install transformers torch"
            )

        cfg = self.manifest["config"]
        model_id = cfg["model"]
        task = cfg.get("task", "text-classification")
        device = cfg.get("device", "cpu")
        max_length = cfg.get("max_length", 512)

        self._max_length = max_length
        self._pipeline = hf_pipeline(
            task,
            model=model_id,
            device=0 if device == "cuda" else -1,
        )
        log.info("loaded huggingface adapter: %s -> %s", self.module_id, model_id)

    def process(self, envelope: dict) -> dict:
        from utils.envelope_factory import now_iso as _now

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
                "timestamp": _now(),
                "meta": {"reason": "empty input"},
            })
            return envelope

        try:
            results = self._pipeline(input_text)

            # Sanitize: convert numpy types to native Python for JSON serialization
            def _sanitize(obj):
                if isinstance(obj, dict):
                    return {k: _sanitize(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [_sanitize(v) for v in obj]
                if hasattr(obj, "item"):
                    return obj.item()
                return obj

            results = _sanitize(results)

            if isinstance(results, list) and len(results) > 0:
                top = results[0]
                label = top.get("label", "neutral")
                score = round(float(top.get("score", 0.0)), 4)
            else:
                label, score = "neutral", 0.0

            envelope["metadata"]["annotations"][self.annotations_key] = {
                "label": label,
                "score": score,
                "raw": results if len(results) <= 5 else results[:5],
            }
            envelope["metadata"]["confidence_scores"][self.annotations_key] = score

            envelope["history"].append({
                "module": self.module_id,
                "input": input_text,
                "output": input_text,
                "status": "success",
                "timestamp": _now(),
                "meta": {"label": label, "score": score},
            })
        except Exception as e:
            envelope["errors"].append({
                "module": self.module_id,
                "error": str(e),
                "timestamp": _now(),
            })

        return envelope

    def unload(self) -> None:
        self._pipeline = None
