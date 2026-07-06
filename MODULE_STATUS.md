# Module Status

Updated when code is committed and tests pass — not when someone says
"I finished."

| Module | Owner | Status |
|---|---|---|
| normalizer | Bhim | DONE, committed, 7 unit tests passing |
| spellcheck | Bhim | DONE, committed, 6 unit tests passing |
| ner | Bhim | DONE, committed, 8 unit tests passing |
| orchestrator core | Bhim | DONE, committed — `run_pipeline(envelope)`, enforces `original_input` immutability, rejects non-dict returns |
| schema + shared utils | Bhim | DONE, committed |
| SCHEMA.md | Bhim | DONE, committed |
| benchmark_sentences.json (10 entries) | Bhim (seed) / Bibek (ongoing growth) | DONE — seed set committed, Bibek to extend as new capabilities land |
| test_integration.py (benchmark runner) | Bibek | DONE, committed — auto-picks up new benchmark entries |
| test_module_integration.py | Biprash | DONE, committed — 7 integration tests |
| run_tests.py | Bibek | DONE, committed — no-pytest runner, verified against pytest for parity |
| sentiment (or other external-team module) | Group Y | not started — pending contact, awaiting `process(envelope)` wrapper |

**Test totals as of last commit:** 41/41 passing via both `pytest tests/ -v` and `python3 run_tests.py`.
