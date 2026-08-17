# NLP Pipeline

Modular Nepali NLP pipeline with plug-and-play modules.
Built for Software Engineering class project.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python cli.py
```

Type a Nepali sentence, press Enter. The pipeline runs every active module
in sequence and shows the result. Type `quit` to exit.

## Web UI

```bash
python run_web.py
```

Then open http://127.0.0.1:5000 in your browser.

- **Analyze** — run any Nepali/English text through the pipeline with
  sentiment, NER highlighting, spellcheck suggestions, stage-by-stage
  audit trail, and the full envelope JSON
- **Modules** — register extension modules from a manifest file or pasted
  JSON, test them, and remove them
- **Config** — view the active pipeline order and registered extensions

## Run Tests

```bash
pytest tests/ -v
# or without pytest:
python run_tests.py
```

## Project Structure

```
modules/          — one file per module, each exposes process(envelope) -> envelope
orchestrator/     — glue code: run_pipeline() and config
utils/            — shared envelope factory, schema validator, logger
tests/            — unit + integration tests
data/             — benchmark sentences
cli.py            — demo REPL
run_web.py        — web UI entry point (Flask)
web/              — Flask app: templates, static assets, pipeline runner
```

## Adding a Module

1. Create `modules/your_module.py` with a `process(envelope) -> envelope` function.
2. Add `"your_module"` to `orchestrator/config.py` `ACTIVE_MODULES` list.
3. Done — the orchestrator picks it up automatically.

## Team

- Bibidh Subedi
- Biprash Pandey
- Bhim Prasad Upadhaya
- Bibek Gautam

## Status

Complete

test
