# Demo Guide: NLP Pipeline with Module Provider System

## What we built

A modular NLP pipeline for Nepali + English text with a **plugin system** that lets anyone plug in their model — whether it's a HuggingFace model, a standalone Python file, or a remote API — through a single JSON manifest.

The whole thing runs from the command line.

---

## How it works (the big picture)

```
┌─────────────────────────────────────────────────────────┐
│                    Module Provider                       │
│  (HuggingFace model / Python code / deployed API)        │
│                                                         │
│  Gives us: a JSON manifest (schema/module_schema.json)   │
└──────────────────────────┬──────────────────────────────┘
                           │
                    register it once
                           │
                           v
┌─────────────────────────────────────────────────────────┐
│                     Registry                             │
│  (registry/registry.py)                                  │
│                                                         │
│  Stores manifests, validates them, creates adapters      │
└──────────────────────────┬──────────────────────────────┘
                           │
                    adapter wraps it
                           │
                           v
┌─────────────────────────────────────────────────────────┐
│              Adapter (one per provider type)             │
│                                                         │
│  code.py       → imports your Python module              │
│  huggingface.py → loads transformers pipeline           │
│  api.py         → POSTs to your HTTP endpoint           │
│                                                         │
│  All three expose: process(envelope) -> envelope         │
└──────────────────────────┬──────────────────────────────┘
                           │
                    same interface
                           │
                           v
┌─────────────────────────────────────────────────────────┐
│              Pipeline (the envelope flows through)       │
│                                                         │
│  normalizer → spellcheck → ner → [your module]          │
│                                                         │
│  Every stage gets the same dict, reads/writes fields,   │
│  appends to history. The pipeline doesn't know or care   │
│  where your module came from.                            │
└─────────────────────────────────────────────────────────┘
```

### The envelope (the data contract)

Every module receives and returns one dict called the **envelope**:

```python
{
  "pipeline_id": "uuid",
  "original_input": "raw text",       # read-only, never changed
  "current_text": "cleaned text",     # modules read/write this
  "encoding": "utf-8",
  "history": [...],                    # append-only log of what ran
  "metadata": {
    "language": "ne",
    "annotations": {                   # each module writes its own key
      "spellcheck": {...},
      "ner": {...},
      "sentiment": {"label": "positive", "score": 0.75}
    },
    "confidence_scores": {}
  },
  "errors": []                         # append-only
}
```

This is defined in `schema/envelope_schema.json`. Modules never touch each other's keys.

### The module manifest (the provider contract)

A provider fills out a JSON file like this:

```json
{
  "module_id": "sentiment-code",
  "name": "Sentiment Analyzer (Built-in)",
  "version": "1.0.0",
  "provider_type": "code",
  "language": ["en", "ne"],
  "behavior": "annotate",
  "annotations_key": "sentiment",
  "config": {
    "entry_point": "modules.sentiment_analyzer"
  }
}
```

Three provider types, three `config` shapes:

| Provider type | Config needs | What the adapter does |
|---|---|---|
| `code` | `entry_point` (dotted Python path) | `importlib.import_module(entry).process(envelope)` |
| `huggingface` | `model` (HF Hub model ID), `task` | `transformers.pipeline(task, model=...)` |
| `api` | `endpoint` (URL) | `requests.post(endpoint, json={"envelope": envelope})` |

The adapter normalizes all three into the same `process(envelope) -> envelope` call. The pipeline never knows the difference.

---

## File structure (what matters)

```
nlp-pipeline/
├── schema/
│   ├── envelope_schema.json      # envelope contract (pre-existing)
│   └── module_schema.json        # manifest contract (NEW)
│
├── registry/
│   ├── adapter.py                # ABC: all adapters implement this
│   ├── registry.py               # stores manifests, creates adapters
│   └── adapters/
│       ├── code.py               # imports Python module
│       ├── huggingface.py        # loads HF transformers pipeline
│       └── api.py                # POSTs to HTTP endpoint
│
├── modules/
│   ├── normalizer.py             # cleans text (pre-existing)
│   ├── spellcheck.py             # spell checker (pre-existing)
│   ├── ner.py                    # named entity recognition (pre-existing)
│   └── sentiment_analyzer.py     # keyword-based sentiment (NEW)
│
├── manifests/
│   ├── sentiment_code.json       # manifest for built-in module
│   ├── sentiment_huggingface.json # manifest for HF model
│   └── sentiment_api.json        # manifest for API endpoint
│
├── scripts/
│   └── mock_sentiment_server.py  # fake API server for demo
│
├── cli.py                        # full CLI (rewritten)
└── orchestrator/
    ├── config.py                 # pipeline stage order
    └── orchestrator.py           # runs modules in sequence
```

---

## Demo script (step by step)

### Before class

```bash
# 1. Make sure you're in the project directory
cd ~/se/nlp-pipeline

# 2. Install deps (if not already)
pip install jsonschema requests
```

### Demo part 1: Basic pipeline (2 min)

```bash
# Show the pipeline running on English text
python3 cli.py run "This is an amazing and wonderful day!"

# Show it on Nepali text — notice NER picks up entities
python3 cli.py run "राम काठमाडौं जान्छ"

# Show negative sentiment
python3 cli.py run "The results were terrible and disappointing"

# Show with JSON output for full envelope
python3 cli.py run "I love this beautiful city" --json
```

**What to point out:**
- Text flows through 4 stages: normalizer → spellcheck → ner → sentiment
- Each stage appends to `history` — full audit trail
- The envelope has `annotations` from each module, keyed by module name
- `original_input` is never modified (provenance preserved)

### Demo part 2: The three provider types (3 min)

#### a) Code provider (already running)

```bash
# The built-in sentiment is a "code" provider
# Show the manifest
cat manifests/sentiment_code.json

# Show the adapter loading it
python3 -c "
from registry.registry import Registry
reg = Registry()
reg.register({'module_id': 'test-code', 'name': 'Test', 'version': '1.0.0',
              'provider_type': 'code', 'config': {'entry_point': 'modules.sentiment_analyzer'}})
adapter = reg.load('test-code')
print('Adapter type:', type(adapter).__name__)
print('Module loaded:', adapter._module)
"
```

#### b) API provider

```bash
# Terminal 1: Start the mock API server
python3 scripts/mock_sentiment_server.py

# Terminal 2: Register and use it
python3 cli.py register manifests/sentiment_api.json
python3 cli.py run "This is terrible and I hate it"

# Show that the pipeline calls out to an HTTP endpoint
# but the output looks identical to the code provider

# Clean up
python3 cli.py remove sentiment-api
```

**What to point out:**
- The API server is just a Python script using `http.server` — could be anyone's Flask/FastAPI service
- The adapter sends the full envelope as JSON, reads back annotations
- The pipeline doesn't care it went over the network

#### c) HuggingFace provider (if transformers is installed)

```bash
python3 cli.py register manifests/sentiment_huggingface.json
python3 cli.py run "This movie was absolutely fantastic!"
python3 cli.py remove sentiment-hf
```

**If transformers isn't installed**, just show the manifest and explain:
```bash
cat manifests/sentiment_huggingface.json
# "model": "cardiffnlp/twitter-xlm-roberta-base-sentiment"
# Same envelope goes in, same envelope comes out
# Just the adapter loads a real neural network instead of keywords
```

### Demo part 3: Registering a new module live (2 min)

```bash
# Show how anyone can add a module in 30 seconds
# 1. Write a manifest
cat > /tmp/my_module.json << 'EOF'
{
  "module_id": "sentiment-api-live",
  "name": "Live API Demo",
  "version": "1.0.0",
  "provider_type": "api",
  "language": ["en"],
  "behavior": "annotate",
  "annotations_key": "sentiment",
  "config": {
    "endpoint": "http://localhost:5001/sentiment",
    "method": "POST",
    "timeout": 10,
    "response_annotations_field": "sentiment",
    "response_confidence_field": "score"
  }
}
EOF

# 2. Register it
python3 cli.py register /tmp/my_module.json

# 3. Run it
python3 cli.py run "This is great"

# 4. Remove it
python3 cli.py remove sentiment-api-live
```

### Demo part 4: CLI overview (1 min)

```bash
# Show all commands
python3 cli.py --help

# List what's registered
python3 cli.py list

# Show pipeline config
python3 cli.py config

# Show the interactive REPL
python3 cli.py demo
# (type a few sentences, show the colored sentiment output)
```

---

## Key talking points

1. **The schema is the contract.** Module providers don't need to read our code — they just fill out a JSON manifest and either ship code, point to a model, or expose an endpoint. We validate their manifest against `module_schema.json` before anything runs.

2. **Three provider types, one interface.** The adapter pattern means the pipeline is provider-agnostic. A HuggingFace model, a local Python file, and a remote API all get normalized into `process(envelope) -> envelope`. The orchestrator never imports `transformers` or `requests`.

3. **Fail-soft design.** If a module crashes, the error is logged into `envelope["errors"]` and the pipeline keeps going. One bad module doesn't kill the whole run.

4. **Envelope = audit trail.** Every module's input/output/status/timestamp is in `history`. You can trace exactly what happened to any piece of text.

5. **Nepali NLP is hard.** The existing normalizer handles Unicode NFC normalization, zero-width character stripping, and Devanagari-specific punctuation rules. The spellchecker uses Levenshtein distance. The NER uses a gazetteer with longest-match-first scanning. Our sentiment module handles both English and Nepali word lists.

---

## Quick troubleshooting

| Problem | Fix |
|---------|-----|
| `python: command not found` | Use `python3` instead |
| `ModuleNotFoundError: No module named 'jsonschema'` | `pip install jsonschema requests` |
| API adapter fails | Make sure `mock_sentiment_server.py` is running on port 5001 |
| HuggingFace adapter fails | `pip install transformers torch` (takes ~2GB) |
| Tests show 2 failures | Pre-existing bugs in `test_envelope_factory` and `test_orchestrator` — not from our changes |
