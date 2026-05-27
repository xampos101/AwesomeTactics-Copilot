"""Fetch AADT markdown files from GitHub using only raw HTTP — no PyGithub.

Strategy:
  1. ONE request to the Git Trees API (returns all repo paths recursively).
  2. N requests to raw.githubusercontent.com (no API key, no rate limits).
"""

from __future__ import annotations

import httpx

from app.config import (
    AADT_CATEGORIES_PREFIX,
    AADT_POSTS_PREFIX,
    GITHUB_BRANCH,
    GITHUB_REPO,
    GITHUB_TOKEN,
)

_MARKDOWN_SUFFIXES = (".md", ".markdown")
_files_cache: dict[str, str] | None = None

_TREE_URL = "https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
_RAW_BASE  = "https://raw.githubusercontent.com/{repo}/{branch}/"


def _auth_headers() -> dict[str, str]:
    token = GITHUB_TOKEN.strip()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _list_markdown_paths(client: httpx.Client) -> list[str]:
    """Single API call — returns all tactic/category markdown paths."""
    url = _TREE_URL.format(repo=GITHUB_REPO, branch=GITHUB_BRANCH)
    resp = client.get(url, headers=_auth_headers())
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 403:
            msg = (
                "GitHub API returned 403. This is usually rate limiting for unauthenticated "
                "requests. Add a token in your `.env` as GITHUB_TOKEN=... then retry. "
                f"URL: {url}"
            )
            raise RuntimeError(msg) from e
        raise
    tree = resp.json().get("tree", [])

    posts_prefix      = AADT_POSTS_PREFIX.rstrip("/") + "/"
    categories_prefix = AADT_CATEGORIES_PREFIX.rstrip("/") + "/"

    return sorted(
        item["path"]
        for item in tree
        if item.get("type") == "blob"
        and item["path"].endswith(_MARKDOWN_SUFFIXES)
        and (
            item["path"].startswith(posts_prefix)
            or item["path"].startswith(categories_prefix)
        )
    )


def _download_raw_files(client: httpx.Client, paths: list[str]) -> dict[str, str]:
    """Download each file via raw.githubusercontent.com (no rate limits)."""
    base = _RAW_BASE.format(repo=GITHUB_REPO, branch=GITHUB_BRANCH)
    files: dict[str, str] = {}
    for path in paths:
        resp = client.get(base + path)
        resp.raise_for_status()
        files[path] = resp.text
    return files


def fetch_aadt_markdown_files(force_refresh: bool = False) -> dict[str, str]:
    """Return {repo_path: file_text} for all tactic/category markdown files.

    Results are cached in memory for the lifetime of the process.
    First call: ~1 API request + N raw downloads (fast, no auth needed).
    Subsequent calls: instant (in-memory cache).
    """
    global _files_cache
    if _files_cache is not None and not force_refresh:
        return _files_cache

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        paths = _list_markdown_paths(client)
        _files_cache = _download_raw_files(client, paths)

    print(f"[github_aadt] fetched {len(_files_cache)} markdown files from GitHub")
    return _files_cache


def clear_aadt_cache() -> None:
    """Drop the in-memory cache (e.g. before a forced re-index)."""
    global _files_cache
    _files_cache = None
