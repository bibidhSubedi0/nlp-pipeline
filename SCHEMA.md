# Communication Schema

## Two-party architecture

```
  Module Provider (HuggingFace / code author / API host)
        |
        |  manifest JSON  (module_schema.json)
        |  + adapter      (code / huggingface / api)
        v
  Registry  ──────>  Adapter.process(envelope)  ──────>  Pipeline
                         |
                    same envelope dict contract as native modules
```

The pipeline does not know or care whether a module came from a local
Python file, HuggingFace Hub, or a remote API. The registry + adapter
system normalizes all three into the same `process(envelope) -> dict`
interface.

## Module Manifest (what a provider gives us)

A provider fills out a JSON manifest validated against
`schema/module_schema.json`. Required fields:

| Field | Type | Description |
|-------|------|-------------|
| `module_id` | string | Unique snake_case ID, e.g. `sentiment-hf` |
| `name` | string | Human-readable name |
| `version` | string | Semantic version `major.minor.patch` |
| `provider_type` | enum | `"huggingface"`, `"code"`, or `"api"` |
| `config` | object | Provider-type-specific config (see below) |

Optional fields: `description`, `language` (ISO 639-1 codes),
`behavior` (`"annotate"` or `"mutate"`), `annotations_key`.

### Config by provider type

**`code`** — provider ships a Python module with `process(envelope)`:
```json
{ "entry_point": "modules.sentiment_analyzer" }
```

**`huggingface`** — provider specifies a HuggingFace model:
```json
{ "model": "cardiffnlp/twitter-xlm-roberta-base-sentiment", "task": "text-classification", "device": "cpu" }
```

**`api`** — provider exposes an HTTP endpoint:
```json
{
  "endpoint": "http://localhost:5001/sentiment",
  "method": "POST",
  "timeout": 30,
  "response_annotations_field": "sentiment",
  "response_confidence_field": "score"
}
```

The API adapter sends the full envelope as `POST { "envelope": <envelope> }`
and reads results back from the response JSON using dot-path field resolution.

## Envelope Schema (per-module data contract)

| Key | Type | Required | Mutability |
|-----|------|----------|------------|
| `pipeline_id` | string (UUID) | yes | read-only |
| `original_input` | string | yes | read-only (orchestrator enforces this) |
| `current_text` | string | yes | read-write — module writes result here |
| `encoding` | string | yes | read-only — always `"utf-8"` |
| `history` | list[dict] | yes | append-only — never modify existing entries |
| `metadata.language` | string | yes | read-only |
| `metadata.annotations` | dict | yes | module writes its own key, never overwrites others |
| `metadata.confidence_scores` | dict | yes | module writes its own key |
| `errors` | list[dict] | yes | append-only |

### History entry schema

Each history entry must have: `module`, `input`, `output`, `status`, `timestamp`, `meta`.

`status` is one of: `success`, `failed`, `skipped`.

Use `skipped` (not `success`) when a module receives empty input and does no
real work — see `modules/normalizer.py`, `modules/spellcheck.py`, and
`modules/ner.py` for the reference pattern.

### Error entry schema

Each error entry must have: `module`, `error`.

## How to build and check an envelope

```python
from utils.envelope_factory import new_envelope
from utils.validate_envelope import validate_envelope

envelope = new_envelope("राम स्कूल जान्छ")   # always start here, never hand-build one
result = your_module.process(envelope)

validate_envelope(result)  # raises if shape is wrong
```

Run `validate_envelope(your_envelope)` after your function returns. If it
raises, the orchestrator will catch it and skip you — better to catch it
yourself first.

## Compatibility rules

- Do not change `utils/envelope_factory.py`, `utils/validate_envelope.py`,
  or `utils/logger.py` unless there's an actual schema bug. These are the
  shared contract — changing them breaks every module.
- If the schema needs to evolve (e.g. add a new field), update
  `REQUIRED_TOP_KEYS`-equivalent logic in `envelope_schema.json` /
  `validate_envelope.py` **and** tell every module owner.
- The orchestrator imports `orchestrator.config` and reads
  `config.ACTIVE_MODULES` fresh on every `run_pipeline()` call — it does
  not cache the list at import time. If you add a module discovery
  mechanism, don't break that lookup path.
- `original_input` is read-only. If your module changes it, the
  orchestrator reverts it and logs an error into `errors` — your module's
  other work still lands, but you'll see the revert in the log.
- Your module must accept and return the *same* envelope dict. Returning
  anything else (a different dict, a string, `None`, etc.) causes the
  orchestrator to reject your output and log an error instead of using it.

## Quick reference: what breaks compatibility

| What you do | What breaks |
|---|---|
| Rename a file in `modules/` | `config.py` still references old name → module skipped |
| Change `process(envelope)` signature | Orchestrator can't call it → exception → fail-soft skip |
| Return something that isn't a dict with required keys | `validate_envelope` raises → module's work discarded |
| Mutate `original_input` | Orchestrator detects and reverts it, logs error |
| Modify existing entries in `history` | Downstream modules see corrupted history (not enforced, but wrong) |
| Write to another module's key in `metadata.annotations` | Overwrites their output silently |
| Add a test function that takes arguments | `run_tests.py` and `pytest` both call `fn()` → `TypeError` |
| Use pytest-only fixtures (`monkeypatch`, `tmpdir`, etc.) | Test passes in pytest but fails in `run_tests.py` |
| Change `utils/validate_envelope.py`'s required fields | Existing modules that passed validation now fail |

## CLI Reference

```
python3 cli.py run <text>              Run full pipeline + registered modules
python3 cli.py run --file <path>       Run on file contents
python3 cli.py list                    List registered modules
python3 cli.py register <manifest.json>  Register a module from manifest
python3 cli.py remove <module_id>      Unregister a module
python3 cli.py config                  Show pipeline configuration
python3 cli.py demo                    Sentiment analysis demo (REPL)
python3 cli.py interactive             Interactive REPL mode
```

## Provider quick-start

### 1. Code provider (simplest)
Write a Python file with `process(envelope: dict) -> dict`. Register it:
```bash
python3 cli.py register manifests/sentiment_code.json
```

### 2. HuggingFace provider
Fill out `manifests/sentiment_huggingface.json` with your model ID.
Requires `pip install transformers torch`.

### 3. API provider
Deploy your model behind an HTTP endpoint. Fill out
`manifests/sentiment_api.json` with the endpoint URL. The adapter
sends `{ "envelope": <envelope> }` and reads results from the response.

Start the mock server for testing:
```bash
python3 scripts/mock_sentiment_server.py  # runs on :5001
python3 cli.py register manifests/sentiment_api.json
python3 cli.py run "This is great!"
```
