"""Load and normalize AADT tactic documents from GitHub."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

import yaml

from app.config import AADT_BASE_URL, AADT_CATEGORIES_PREFIX, AADT_POSTS_PREFIX
from ingestion.github_aadt import fetch_aadt_markdown_files

_POSTS_PREFIX = AADT_POSTS_PREFIX.rstrip("/") + "/"
_CATEGORIES_PREFIX = AADT_CATEGORIES_PREFIX.rstrip("/") + "/"


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Extract YAML front-matter and body from a markdown file."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    body = match.group(2).strip()
    return meta, body


def _category_files(files: dict[str, str]) -> dict[str, str]:
    return {
        path: text
        for path, text in files.items()
        if path.replace("\\", "/").startswith(_CATEGORIES_PREFIX)
        and path.endswith((".md", ".markdown"))
    }


def _post_files(files: dict[str, str]) -> dict[str, str]:
    return {
        path: text
        for path, text in files.items()
        if path.replace("\\", "/").startswith(_POSTS_PREFIX)
        and path.endswith((".md", ".markdown"))
    }


def load_categories_from_files(files: dict[str, str]) -> dict[str, dict[str, str]]:
    """Return {category_name: {description, type}} from markdown paths + content."""
    categories: dict[str, dict[str, str]] = {}
    for path, raw in sorted(_category_files(files).items()):
        meta, _ = _parse_frontmatter(raw)
        name = meta.get("category-name", PurePosixPath(path).stem)
        categories[name] = {
            "description": meta.get("category-description", ""),
            "type": meta.get("category-type", ""),
        }
    return categories


def load_tactics_from_files(files: dict[str, str]) -> list[dict[str, Any]]:
    """Parse tactic posts from markdown paths + content."""
    tactics: list[dict[str, Any]] = []

    for path, raw in sorted(_post_files(files).items()):
        meta, body = _parse_frontmatter(raw)
        if not meta.get("title"):
            continue

        title = meta["title"].strip('" ')
        category = meta.get("categories", "unknown")
        if isinstance(category, list):
            category = category[0]
        category = str(category).strip()

        tactic_type = meta.get("t-sort", "Unknown").strip('" ')

        tags_raw = meta.get("tags", "")
        if isinstance(tags_raw, list):
            tags = tags_raw
        else:
            tags = [t.strip() for t in str(tags_raw).split() if t.strip()]

        description = str(meta.get("t-description", "")).strip('" ')
        intent = str(meta.get("t-intent", "")).strip('" ')
        measured_impact = str(meta.get("t-measuredimpact", "")).strip('" ')
        source = str(meta.get("t-source", "")).strip('" ')
        source_doi = str(meta.get("t-source-doi", "")).strip('" ')
        countermeasure = str(meta.get("t-countermeasure", "")).strip('" ')

        slug = PurePosixPath(path).stem
        date_prefix = re.match(r"\d{4}-\d{2}-\d{2}-", slug)
        if date_prefix:
            slug = slug[date_prefix.end() :]
        url = f"{AADT_BASE_URL}/{category}/{slug}/"

        full_text_parts = [
            f"Title: {title}",
            f"Category: {category}",
            f"Type: {tactic_type}",
            f"Description: {description}" if description else "",
            f"Intent: {intent}" if intent else "",
            f"Measured Impact: {measured_impact}" if measured_impact else "",
            f"Countermeasure: {countermeasure}" if countermeasure else "",
            f"Source: {source}" if source else "",
        ]
        full_text = "\n".join(p for p in full_text_parts if p)
        if body:
            full_text += "\n\n" + body

        tactics.append(
            {
                "title": title,
                "category": category,
                "tactic_type": tactic_type,
                "description": description,
                "tags": tags,
                "participant": str(meta.get("t-participant", "")).strip('" '),
                "context": str(meta.get("t-context", "")).strip('" '),
                "intent": intent,
                "target_qa": str(meta.get("t-targetQA", "")).strip('" '),
                "related_qa": str(meta.get("t-relatedQA", "")).strip('" '),
                "measured_impact": measured_impact,
                "countermeasure": countermeasure,
                "source": source,
                "source_doi": source_doi,
                "url": url,
                "file_path": path,
                "full_text": full_text,
            }
        )
    return tactics


def load_categories() -> dict[str, dict[str, str]]:
    """Fetch AADT category metadata from GitHub."""
    files = fetch_aadt_markdown_files()
    return load_categories_from_files(files)


def load_tactics() -> list[dict[str, Any]]:
    """Fetch and parse all AADT tactic posts from GitHub."""
    files = fetch_aadt_markdown_files()
    return load_tactics_from_files(files)


if __name__ == "__main__":
    cats = load_categories()
    print(f"Loaded {len(cats)} categories")
    for name, info in cats.items():
        print(f"  {name}: {info['type']}")

    docs = load_tactics()
    print(f"\nLoaded {len(docs)} tactics")
    for d in docs[:5]:
        print(f"  [{d['tactic_type']}] {d['title']} ({d['category']})")
