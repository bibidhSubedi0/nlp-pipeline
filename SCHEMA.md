# Envelope Schema

Every module receives and returns this dict:

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
