"""Retrieve relevant tactics from the Chroma vector index."""

from __future__ import annotations

import json
from typing import Any

from ingestion.build_index import get_collection


def retrieve_tactics(
    query: str,
    n_results: int = 8,
    category_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Return top-k tactics matching the query, optionally filtered by category.

    Each result dict includes: title, category, tactic_type, description (the
    full_text chunk), source, source_doi, url, intent, target_qa, tags, and
    the similarity distance.
    """
    collection = get_collection()

    where_filter = None
    if category_filter:
        where_filter = {"category": category_filter}

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    tactics: list[dict[str, Any]] = []
    if not results["documents"] or not results["documents"][0]:
        return tactics

    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        tags = meta.get("tags", "[]")
        try:
            tags = json.loads(tags)
        except (json.JSONDecodeError, TypeError):
            tags = [tags] if tags else []

        tactics.append(
            {
                "title": meta.get("title", ""),
                "category": meta.get("category", ""),
                "category_type": meta.get("category_type", ""),
                "tactic_type": meta.get("tactic_type", ""),
                "description": doc,
                "source": meta.get("source", ""),
                "source_doi": meta.get("source_doi", ""),
                "url": meta.get("url", ""),
                "intent": meta.get("intent", ""),
                "target_qa": meta.get("target_qa", ""),
                "tags": tags,
                "distance": dist,
            }
        )
    return tactics


def format_context(tactics: list[dict[str, Any]]) -> str:
    """Format retrieved tactics into a numbered text block for the LLM prompt."""
    if not tactics:
        return "(No relevant tactics were found in the AADT catalog.)"

    parts: list[str] = []
    for i, t in enumerate(tactics, 1):
        parts.append(
            f"[{i}] {t['title']}\n"
            f"    Category: {t['category']}\n"
            f"    Type: {t['tactic_type']}\n"
            f"    Source: {t['source']}\n"
            f"    DOI: {t['source_doi']}\n"
            f"    URL: {t['url']}\n"
            f"    ---\n"
            f"    {t['description']}\n"
        )
    return "\n".join(parts)
