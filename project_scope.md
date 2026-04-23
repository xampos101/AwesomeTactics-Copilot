# Agentic Tactics Copilot — Project Scope

**Project:** Agentic Tactics Copilot  
**Team:** 2 people  
**Internship:** VU Amsterdam, S2 Lab  
**Timeline:** ~4 weeks (until 30 May 2026)

---

## One-Line Statement

> An Agentic Tactics Copilot that uses RAG over AwesomeAndDarkTactics (AADT) and Nebula-backed LLMs to recommend, critique, compare, and safely generate tactic reports.

---

## Problem

Software architects and developers need guidance on sustainable, responsible software design choices. The AADT catalog contains curated Awesome Tactics (good practices) and Dark Tactics (harmful patterns), but it is a static resource — users must manually search and interpret it. There is no intelligent assistant that can reason over this knowledge base and provide personalized, grounded advice.

---

## Goal

Build a RAG-based AI assistant that:
1. **Recommends** relevant tactics for a given scenario
2. **Critiques** a design choice and identifies dark tactic risks
3. **Compares** two or more tactics with trade-offs
4. **Grounds every answer** in AADT sources (with citations)
5. **(Agent extension)** Safely creates/edits markdown reports based on its analysis

---

## Knowledge Base

| Source | Content |
|---|---|
| [AADT Catalog](https://s2group.cs.vu.nl/AwesomeAndDarkTactics/catalog.html) | 8 categories: cloud-computing, edge-computing, green-ml-enabled-systems, green-software-practice, resource-adaptation, resource-allocation, resource-monitoring, socially-centered-practices |
| [AADT GitHub Repo](https://github.com/S2-group/AwesomeAndDarkTactics) | Markdown files per tactic with metadata, description, trade-offs |

---

## Architecture

```
[Streamlit UI]
     |
     +-- Chat / Agent Tasks / Benchmark
           |
     [LangChain Orchestrator]
           |
     +-----+------------------+
     |                        |
[Retriever]             [Agent Tools]
(FAISS/Chroma           - read input brief
 over AADT docs)        - create markdown report
     |                  - edit template (with approval)
[Context + citations]
     |
[LLM Provider]
  Nebula (open-source Ollama models)
  + optional commercial (OpenAI/Anthropic)
     |
[Structured Output]
  recommendation + trade-offs + risks + citations
```

---

## Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| Orchestration | LangChain |
| Vector DB | FAISS or Chroma |
| Embeddings | sentence-transformers or Nebula-compatible |
| LLM (open-source) | Nebula (Ollama: llama3, mistral, deepseek-r1, etc.) |
| LLM (commercial) | OpenAI GPT-4o or Anthropic Claude |
| Language | Python 3.11 |

---

## MVP Features (Phase 1–2)

- [x] RAG chat over AADT knowledge base
- [x] 3 chat modes: `recommend`, `critique`, `compare`
- [x] Source citations in every answer
- [x] Streamlit chat UI with mode selector
- [x] Nebula model backend
- [x] Optional commercial model connector

## Agent Extension (Phase 3)

- [ ] Read project brief from user file upload
- [ ] Generate markdown report (`tactics_analysis.md`)
- [ ] Edit existing markdown template
- [ ] **Always require user approval before writing**
- [ ] **Write restricted to `/reports` folder only**

---

## Benchmark Plan (Phase 5)

- **Dataset:** 30 benchmark questions (10 recommend / 10 critique / 10 compare+adversarial)
- **Models compared:** 2 Nebula open-source models + 1 commercial model
- **Metrics:** groundedness, answer quality, hallucination rate, latency, cost/query

---

## Team Split

| Person A (Tactics & Agent) | Person B (Data & Infrastructure) |
|---|---|
| Prompt design (3 modes) | Data ingestion from AADT |
| Output schema | Retriever + vector DB |
| Agent workflow + guardrails | Nebula + commercial connectors |
| Evaluation rubric | Streamlit skeleton + benchmark tab |

---

## Scope Boundaries (what we will NOT do)

- No autonomous code rewriting or editing application source files
- No write actions without explicit user confirmation
- No out-of-AADT hallucinated recommendations (source-grounded first)
- No full autonomous agent in Phase 1 (advisor only)

---

## Phases

| Phase | Goal | Duration |
|---|---|---|
| 0 | Alignment + setup | 1 day |
| 1 | Data ingestion + vector store | 2–3 days |
| 2 | RAG advisor MVP | 2–3 days |
| 3 | Agent layer (safe file actions) | 3–4 days |
| 4 | Streamlit app | 2 days |
| 5 | Benchmark + evaluation | 2–3 days |
| 6 | Final packaging + demo | 1–2 days |
