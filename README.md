# Clinical Trial Matcher

A LangGraph-based pipeline that matches a free-text patient profile to recruiting clinical trials.

The project:
- extracts structured entities from patient text (diseases, medications, genes, age),
- searches ClinicalTrials.gov for candidate studies,
- scores each trial with an LLM (Groq),
- generates a ranked markdown report.

## Pipeline Overview

Input:
- `patient_profile` (free-text string)

Flow:
1. **Extractor** (`agents/extractor.py`)  
   Uses OpenMed NER models + regex fallback for age extraction.
2. **Searcher** (`agents/searcher.py`)  
   Queries ClinicalTrials.gov v2 API for recruiting studies.
3. **Matcher** (`agents/matcher.py`)  
   Uses Groq (`llama-3.3-70b-versatile`) to score trial fit.
4. **Explainer** (`agents/explainer.py`)  
   Produces the final ranked markdown report.

Graph wiring is in `graph.py` using `StateGraph(ClinicalTrialState)`.  
If no candidate trials are found, the graph skips matcher and goes straight to explainer.

## Project Structure

```text
agents/
  extractor.py
  searcher.py
  matcher.py
  explainer.py
config/
  config.py
  state.py
  database.py
scripts/
  run_pipeline.py
tests/
main.py
graph.py
```

## Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) for environment and dependency management
- Access to external APIs/services used by the pipeline

## Setup

From the repository root:

```bash
python -m pip install uv
~/.local/bin/uv sync
cp .env.example .env
```

Set the required variables in `.env`:

- `GROQ_API_KEY` (required)
- `MONGODB_URI` (required)
- `MONGODB_DB_NAME` (optional, default: `trial_matcher`)

## Run

Run the main pipeline with the sample patient profile:

```bash
~/.local/bin/uv run python main.py
```

Run and persist pipeline execution metadata/results in MongoDB:

```bash
~/.local/bin/uv run python scripts/run_pipeline.py
```

## Testing

Run all tests:

```bash
~/.local/bin/uv run pytest
```

Run unit tests only (no live external API calls intended):

```bash
~/.local/bin/uv run pytest tests/test_unit_searcher.py tests/test_unit_matcher.py -v
```

Run smoke/integration-style tests:

```bash
~/.local/bin/uv run pytest tests/test_extractor.py tests/test_searcher.py tests/test_matcher.py tests/test_pipeline.py tests/test_db_integration.py -v
```

> Note: smoke/integration tests rely on external services and valid credentials.

## Configuration

Runtime settings are defined in `config/config.py`:
- `max_candidate_trials` (default `20`)
- `top_n_trials` (default `5`)
- `min_match_score` (default `40`)

## Data Model

Core state and models are in `config/state.py`:
- `ExtractedEntities`
- `CandidateTrial`
- `ScoredTrial`
- `ClinicalTrialState`

Each LangGraph node returns only updated keys, and LangGraph merges them into the full state.