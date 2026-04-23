"""RAG pipeline: route user queries through mode-specific prompts and LLM."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from openai import OpenAI

from app.config import ProviderConfig
from app.prompts import MODE_PROMPTS, SYSTEM_PROMPT
from rag.retriever import format_context, retrieve_tactics

logger = logging.getLogger(__name__)


def _call_llm(
    provider: ProviderConfig,
    system: str,
    user_message: str,
    temperature: float = 0.2,
) -> tuple[str, float]:
    """Send a chat completion request, return (response_text, latency_seconds)."""
    client = OpenAI(
        base_url=provider.api_base,
        api_key=provider.api_key or "no-key",
    )
    t0 = time.time()
    response = client.chat.completions.create(
        model=provider.model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=2048,
    )
    latency = time.time() - t0
    text = response.choices[0].message.content or ""
    return text, latency


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Best-effort extraction of JSON from an LLM response string."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {"raw_response": raw, "parse_error": True}


def run_query(
    user_query: str,
    mode: str,
    provider: ProviderConfig,
    n_results: int = 8,
    category_filter: str | None = None,
) -> dict[str, Any]:
    """Execute the full RAG pipeline for a single query.

    Returns a dict with the parsed LLM output, retrieved sources, and metadata.
    """
    if mode not in MODE_PROMPTS:
        return {"error": f"Unknown mode: {mode}. Use recommend/critique/compare."}

    tactics = retrieve_tactics(user_query, n_results=n_results, category_filter=category_filter)
    context = format_context(tactics)
    prompt_template = MODE_PROMPTS[mode]

    if mode == "agent_analyze":
        user_prompt = prompt_template.format(
            file_content=user_query,
            retrieved_context=context,
        )
    else:
        user_prompt = prompt_template.format(
            user_query=user_query,
            retrieved_context=context,
        )

    try:
        raw_response, latency = _call_llm(provider, SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        logger.exception("LLM call failed")
        return {"error": str(e), "provider": provider.name}

    parsed = _parse_json_response(raw_response)

    return {
        "parsed": parsed,
        "raw_response": raw_response,
        "retrieved_tactics": [
            {
                "title": t["title"],
                "category": t["category"],
                "tactic_type": t["tactic_type"],
                "source": t["source"],
                "source_doi": t["source_doi"],
                "url": t["url"],
                "distance": t["distance"],
            }
            for t in tactics
        ],
        "provider": provider.name,
        "model": provider.model,
        "latency_seconds": latency,
        "mode": mode,
    }
