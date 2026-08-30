# Structured Extraction Pipeline

Built a Python pipeline that extracts structured, validated data from unstructured text (job postings) using an LLM, guaranteeing type-safe output even when the model returns malformed or invalid responses.

Schema-validated extraction of structured data from messy, unstructured text (job postings) using an LLM.

Designed a Pydantic schema as the extraction contract, with field-level descriptions doubling as prompt guidance sent directly to the model
Implemented a bounded retry loop that feeds validation errors back to the LLM as repair instructions rather than discarding failures, with full per-attempt logging for observability
Built a swappable LLM client interface (tested locally via Ollama) and an 8-test suite using a scripted fake client for deterministic, zero-cost testing
Created a labeled evaluation harness across real job postings, scoring per-field accuracy and uncovering a reproducible extraction failure traced to input phrasing rather than model or schema design

Tech: Python, Pydantic, pytest, LLM APIs (Anthropic/local via Ollama)

## What this project does

`Structured Extraction Pipeline` takes free-text job postings and turns them into validated Python objects (Pydantic models) — reliably, even when the LLM returns malformed output. The core idea: when the model's response fails validation, the validation error itself is sent back to the model as a follow-up instruction ("here's what's wrong, fix it"), instead of just failing or blindly retrying. This repeats up to a fixed number of attempts before giving up and raising a well-documented failure.

This is a personal learning project (see `Structured _Extraction_Pipeline_NOTES.md`) built to understand, from first principles, the pattern that libraries like Instructor or LangChain's output parsers implement for you. It also doubles as a working example of test-driven Python development, since the full behavior is pinned down by a pytest suite before/alongside the implementation.

## How it works, in short

```
text -> prompt(schema) -> LLM -> raw string
                                   |
                        json.loads + model_validate
                                   |
              +--------------------+-------------------+
          valid                                  ValidationError
            |                                          |
        return obj                  append error text -> retry (max 3)
                                                       |
                                            exhausted -> log + raise
```

1. A Pydantic model (`JobPosting`) defines the target schema — field names, types, and human-readable `Field(description=...)` hints.
2. That schema is serialized to JSON Schema and embedded directly in the prompt sent to the LLM, so the Python class *is* the source of truth for what the model is asked to return.
3. The model's raw text response is parsed and validated against the schema.
4. If validation fails, the structured Pydantic error (which fields are wrong, why, and what value caused it) is appended to a new "repair" prompt and sent back to the model.
5. This repeats up to `max_attempts` (default 3). Every attempt — including the raw response and any error — is recorded, so a permanent failure has a full forensic record instead of a silent drop.

## Project structure

```
c1-extractor/
├── extractor.py          # Core logic: build_prompt, build_repair_prompt, extract()
├── test_extractor.py     # Pytest spec (8 tests) that extract() must satisfy; defines the "main" JobPosting schema
├── clients.py             # LLM client interface: FakeClient (scripted/offline) and OllamaClient (local model over HTTP)
├── responses.py           # Canned model responses (good, malformed, fenced, prose) used by tests and FakeClient
├── demo.py                 # Runs extract() end-to-end against a real or fake client, with logging
├── eval_set.py             # 6 hand-labeled (text, expected_dict) examples, incl. 2 real scraped postings
├── eval.py                 # Runs the eval set through extract() and scores per-field accuracy
├── anthropic/               # Separate, smaller experiment calling the real Anthropic Claude API directly
│   ├── extract.py            # One-shot script: build prompt from schema, call Claude, parse response (no retry loop)
│   ├── jobschema.py           # A larger/rougher JobPosting schema used only by this subfolder's experiment
│   └── client.py               # Empty/unused placeholder file
├── Structured_Extraction_Pipeline_NOTES.md              # Detailed session notes: concepts learned, bugs found, interview talking points
├── PYTHON_CRASH_COURSE.md   # An 8-block Python tutorial built from this project's own code
├── repsonses                # Empty, 0-byte stray file (likely a typo of responses.py; safe to ignore/delete)
├── .env                      # Holds ANTHROPIC_API_KEY (not committed — see .gitignore)
└── .gitignore                # Ignores .venv/, __pycache__/, .env, .pytest_cache/
```

## Two parallel tracks in this repo

1. **The main project (repo root).** Uses a local model via Ollama (`clients.py` → `OllamaClient`), the full retry/validation loop (`extractor.py`), and is covered by tests (`test_extractor.py`) and a labeled eval (`eval_set.py` / `eval.py`). This is where the actual "C1" lesson — retry-on-validation-error — lives.
2. **The `anthropic/` subfolder.** A smaller, separate exploration that calls the real Claude API (`anthropic/extract.py`) directly with a bigger, messier schema (`anthropic/jobschema.py`), without the retry loop. It's a one-shot script, not wired into the tested extraction pipeline.

## Requirements

- Python 3.10+ (uses `X | None` union syntax)
- `pydantic` (v2)
- `pytest` (for `test_extractor.py`)
- `requests` (only needed if using `OllamaClient`, plus a local `ollama serve` running)
- `anthropic` and `python-dotenv` (only needed for the `anthropic/` subfolder scripts)

## Running things

```bash
# Run the test suite (free — uses FakeClient, no network calls)
pytest test_extractor.py -v

# Run the end-to-end demo against a local Ollama model
# (requires `ollama serve` running and a model pulled, e.g. llama3.2)
python demo.py

# Run the labeled evaluation and see per-field accuracy
python eval.py

# Run the standalone Anthropic API experiment (needs ANTHROPIC_API_KEY in .env)
cd anthropic && python extract.py
```

## Security note

`.env` in this folder contains a live `ANTHROPIC_API_KEY`. It's already listed in `.gitignore` so it won't be committed, but treat it as a secret — don't paste it into chats, screenshots, or public code.
