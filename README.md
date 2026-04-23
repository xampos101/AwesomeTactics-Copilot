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

### 2. Clone the AADT knowledge base (if not already present)

```bash
git clone https://github.com/S2-group/AwesomeAndDarkTactics.git data/aadt-repo
```

### 3. Build the vector index

```bash
python -m ingestion.build_index
```

### 4. Configure LLM providers

Copy `.env.example` to `.env` and set your keys:

```bash
cp .env.example .env
```

Edit `.env`:
```
NEBULA_API_BASE=http://your-nebula-host:11434/v1
NEBULA_MODEL_1=llama3
NEBULA_MODEL_2=mistral
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
```

If you don't set any providers, the sidebar will show manual configuration fields.

### 5. Run the app

```bash
streamlit run app/main.py
```

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
  load_aadt.py     — Parse AADT markdown tactics + metadata
  build_index.py   — Chunk, embed, index into Chroma
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
  aadt-repo/       — Cloned AADT repository
  chroma_db/       — Persisted vector index
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
