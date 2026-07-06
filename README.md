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

