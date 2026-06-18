# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A LangGraph-based pipeline that matches patient profiles to clinical trials. Given a free-text patient profile, it extracts medical entities (diseases, medications, genes, age) and scores candidate trials from MongoDB against those entities using an LLM (Groq).

## Environment Setup

Requires Python 3.11. Uses `uv` for dependency management.

```bash
uv sync                  # install dependencies into .venv
cp .env.example .env     # create env file (see required vars below)
```

Required `.env` variables:
- `GROQ_API_KEY` — Groq LLM API key
- `MONGODB_URI` — MongoDB connection string
- `MONGODB_DB_NAME` — defaults to `trial_matcher`

## Commands

```bash
uv run python main.py                         # run the app
uv run python tests/test_extractor.py         # run the extractor smoke test
uv run pytest                                 # run all tests
uv run pytest tests/test_extractor.py -v      # run a single test file
```

## Architecture

The pipeline is a LangGraph graph where each node reads from and writes to `ClinicalTrialState` (defined in `config/state.py`). Nodes return only the keys they modify; LangGraph merges the result into the full state.

### Pipeline Flow

```
patient_profile (str)
    → extractor_node        [agents/extractor.py]
    → searcher_node         [agents/searcher.py] fetches candidate_trials from ClinicalTrials.gov v2 API
    → matcher_node          [agents/matcher.py] LLM scores each trial → scored_trials
    → explainer_node        [agents/explainer.py] LLM generates final markdown report
```

### Key files

| File | Purpose |
|---|---|
| `config/state.py` | `ClinicalTrialState` TypedDict + Pydantic models (`ExtractedEntities`, `ScoredTrial`) |
| `config/config.py` | `Settings` (pydantic-settings, reads from `.env`) — imported as `settings` singleton |
| `config/database.py` | MongoDB client setup (currently empty) |
| `agents/extractor.py` | NER extraction using three specialized OpenMed models |
| `agents/searcher.py` | Queries ClinicalTrials.gov v2 API using extracted entities to fetch candidate trials |
| `agents/matcher.py` | Uses Groq LLM to score candidate trials against patient profile |
| `agents/explainer.py` | Uses Groq LLM to generate the final markdown report from scored trials |
| `graph.py` | LangGraph `StateGraph` wiring all four nodes; conditional edge skips matcher when no trials found |
| `main.py` | Entry point — runs the full pipeline on a hardcoded patient profile |
| `tests/test_extractor.py` | Smoke test for the extractor node — runs against live OpenMed API |
| `tests/test_searcher.py` | Smoke test for the searcher node — queries ClinicalTrials.gov v2 API |
| `tests/test_matcher.py` | Smoke test for the matcher node — scores trials using Groq LLM |
| `tests/test_pipeline.py` | End-to-end pipeline test — patient profile → final markdown report |

### Extractor agent

Uses three OpenMed NER models in sequence, each specialized for a different entity type:
- `OpenMed-NER-DiseaseDetect-BioMed-335M` — diseases
- `OpenMed-NER-ChemicalDetect-ElectraMed-33M` — medications/chemicals
- `OpenMed-NER-GenomicDetect-PubMed-109M` — genes

Filters to `score > 0.85` and deduplicates via sets. Age is extracted with a regex fallback (`\d{2}[- ]?year[- ]?old`).

The `_client = OpenMed()` is module-level to avoid reloading model weights on every pipeline invocation.

### Searcher agent

Queries `https://clinicaltrials.gov/api/v2/studies` with:
- `query.cond` — diseases from entities, joined with ` OR `
- `query.intr` — medications from entities, joined with ` OR `
- `filter.overallStatus=RECRUITING` — only active trials
- `pageSize=settings.max_candidate_trials`

Extracts flat dicts with `nct_id`, `title`, `phase`, `status`, `eligibility`, `url` from the v2 API response structure.

### Matcher agent

Uses Groq LLM (`llama-3.3-70b-versatile`) with structured output (Pydantic `TrialScore`) to score each candidate trial. For each trial:
1. Formats patient entities as plain-text summary (diseases, medications, genes, age)
2. Sends to LLM with trial title, phase, eligibility text
3. LLM returns validated JSON: score (0–100), matching_criteria (list[str]), exclusion_flags (list[str])
4. Filters trials below `settings.min_match_score`, sorts by score descending, takes top `settings.top_n_trials`

Returns `list[ScoredTrial]` — each with `nct_id`, `title`, `phase`, `score`, `matching_criteria`, `exclusion_flags`, `trial_url`.

### Explainer agent

Uses Groq LLM (free-text output, no structured output) to generate the final markdown report. Receives scored trials + patient entities, returns a `final_report` string with ranked trial recommendations, plain-language explanations, and eligibility flags. Returns a "no trials found" fallback if `scored_trials` is empty.

### Graph (`graph.py`)

`StateGraph(ClinicalTrialState)` with a conditional edge after the searcher:
- If `candidate_trials` is empty → skip matcher, go directly to explainer
- Otherwise → matcher → explainer

Run the full pipeline: `graph.invoke({...initial state...})`

### Settings

`config/config.py` exposes a `settings` singleton with tunable pipeline parameters:
- `max_candidate_trials` (default 20) — how many trials to retrieve from the API
- `top_n_trials` (default 5) — how many to surface in the final report
- `min_match_score` (default 40) — minimum score threshold for a trial to be included