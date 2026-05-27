# Agentic Tactics Copilot

A RAG-powered AI assistant that recommends, critiques, and compares software architecture tactics from the [AwesomeAndDarkTactics (AADT)](https://s2group.cs.vu.nl/AwesomeAndDarkTactics/catalog.html) catalog. Includes an agent layer for safe markdown report generation and a benchmark system for comparing open-source vs commercial LLMs.

## Features

- **RAG Chat** — Ask questions and get grounded answers with AADT citations
  - `recommend`: suggests tactics for a given scenario
  - `critique`: evaluates a design decision for dark tactic risks
  - `compare`: side-by-side comparison of tactics with trade-offs
- **Agent Mode** — Upload a project brief, get an analysis report, and save it with approval
- **Benchmark** — Run the 30-question evaluation set across multiple models and compare scores
- **Guardrails** — Never recommends dark tactics as desirable; always cites sources; refuses to fabricate

## Architecture

```
Streamlit UI (Chat / Agent Tasks / Benchmark)
    |
LangChain-style Orchestrator
    |
+---+-------------------+
|                       |
Retriever             Agent Tools
(Chroma over          - read input
 164 AADT tactics)    - create/edit reports
    |                 - approval gate
Context + metadata
    |
LLM Provider
  Nebula (open-source) / OpenAI (commercial)
    |
Structured JSON Output
  + citations + scores
```

## Quick Start

### 1. Clone and setup

```bash
git clone <this-repo>
cd "Tactics AI"
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and set LLM keys. For indexing, optionally set `GITHUB_TOKEN` (raises API rate limits; public repo works without it).

```bash
cp .env.example .env   # Windows: copy .env.example .env
```

### 3. Build the vector index

Fetches tactic markdown from GitHub (`S2-group/AwesomeAndDarkTactics`) and embeds into `data/chroma_db`. Re-runs are fast if the index already exists.

```bash
python -m ingestion.build_index
```

### 4. Configure LLM providers

Edit `.env` (LLM section):
```
NEBULA_API_BASE=http://your-nebula-host:11434/v1
NEBULA_MODEL_1=llama3
NEBULA_MODEL_2=mistral
NEBULA_API_KEY=<your nebula api key or 'nebula'>
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
```

If you don't set any provider models, the app defaults to Nebula with `llama3` (using `NEBULA_API_BASE`).

### 5. Run the app

```bash
streamlit run app/main.py
```

## Website integration (floating chat widget)

This repo now also ships a tiny HTTP API + embeddable widget (a small circle button that opens a side panel).

### 1) Run the API server

```bash
uvicorn app.server:app --reload --port 8000
```

### 2) Embed on your tactics website

Add this to the website HTML (e.g. your Jekyll layout/footer):

```html
<script
  src="http://localhost:8000/widget.js"
  data-api-base="http://localhost:8000"
  data-title="Tactics Copilot"
  data-subtitle="Ask about tactics"
  data-mode="recommend"
  data-top-k="8"
></script>
```

### Notes

- The widget calls `POST /api/chat` on this server.
- On first start (or missing index), the server fetches AADT markdown from GitHub and builds/uses the Chroma index in `data/chroma_db`. Later starts reuse the local index only.
- To allow the website domain to call the API, set:
  - `CORS_ALLOW_ORIGINS=https://s2group.cs.vu.nl,https://your-domain.example`

## Running Benchmarks

### Via the UI
Go to the **Benchmark** tab, select models, choose how many questions, and click Run.

### Via CLI
```bash
python -m evaluation.run_benchmark          # all 30 questions
python -m evaluation.run_benchmark 10       # first 10 questions
```

Results are saved to `evaluation/benchmark_results_<timestamp>.json`.

## Project Structure

```
app/
  main.py          — Streamlit UI (Chat, Agent, Benchmark tabs)
  config.py        — Provider config, Pydantic schemas, paths
  prompts.py       — Frozen prompt templates + guardrails (v1.1)
ingestion/
  github_aadt.py   — Fetch AADT markdown from GitHub API
  load_aadt.py     — Parse tactics + category metadata
  build_index.py   — Embed and index into Chroma
rag/
  retriever.py     — Top-k retrieval with optional category filter
  pipeline.py      — Mode routing + LLM call + JSON parsing
agent/
  workflow.py      — Document analysis pipeline
  report_writer.py — Safe markdown write/edit with path guards
evaluation/
  benchmark_questions.json — 30 benchmark questions
  run_benchmark.py — Batch runner across models
  score.py         — Groundedness, citation, parse, safety metrics
reports/           — Generated report artifacts
data/
  chroma_db/       — Persisted vector index (GitHub fetch only when building)
```

## Benchmark Metrics

| Metric | Description |
|---|---|
| Groundedness | How many tactic names in the answer match retrieved context |
| Citation Presence | Whether the answer includes source references |
| Parse Success | Whether the LLM returned valid JSON |
| Dark Tactic Safety | For adversarial questions: did the model refuse to recommend dark tactics? |
| Latency | Response time in seconds |

## Knowledge Base

164 tactics across 9 categories from the AADT catalog:
- cloud-computing (Dark Tactics)
- edge-computing (Dark Tactics)
- green-ml-enabled-systems (Awesome Tactics)
- green-software-practice (Awesome Tactics)
- resource-adaptation (Awesome Tactics)
- resource-allocation (Awesome Tactics)
- resource-monitoring (Awesome Tactics)
- socially-centered-practices (Awesome Tactics)
- templates

## Tech Stack

- Python 3.11+
- Streamlit
- LangChain (concepts) + OpenAI client
- ChromaDB + sentence-transformers (all-MiniLM-L6-v2)
- PyGithub (GitHub Contents API for AADT markdown)
- Nebula / Ollama (open-source LLMs)
- OpenAI API (commercial LLM)
- Plotly + Pandas (benchmark visualization)

## Limitations

- Answer quality depends on the LLM model; smaller open-source models may not always produce valid JSON
- Retrieval is embedding-based; short or abstract tactic descriptions may have lower recall
- Agent mode writes only markdown to `/reports`; no code modification capability
- Benchmark scoring is automated heuristic-based, not human-evaluated

## License

Academic project — VU Amsterdam, S2 Lab.
