"""Safe markdown report writer with guardrails.

All write operations are restricted to the REPORTS_DIR and require
explicit caller confirmation before executing.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from app.config import REPORTS_DIR

logger = logging.getLogger(__name__)


class ReportWriteError(Exception):
    """Raised when a write operation violates safety constraints."""


def _validate_filename(name: str) -> str:
    """Sanitize and validate a report filename.

    Rejects any path components (slashes, ..) to prevent directory traversal.
    """
    name = name.strip()
    if not name:
        raise ReportWriteError("Filename cannot be empty.")
    if "/" in name or "\\" in name or ".." in name:
        raise ReportWriteError(
            f"Filename must not contain path separators or '..': {name!r}"
        )
    name = re.sub(r"[^\w\-. ]", "_", name)
    if not name.endswith(".md"):
        name += ".md"
    return name


def _ensure_within_reports_dir(path: Path) -> None:
    """Verify path resolves inside REPORTS_DIR."""
    resolved = path.resolve()
    if not str(resolved).startswith(str(REPORTS_DIR.resolve())):
        raise ReportWriteError(
            f"Write rejected: {resolved} is outside the allowed reports directory."
        )


def save_report(content: str, filename: str = "tactics_analysis.md") -> Path:
    """Write a markdown report to the reports directory.

    Args:
        content: The markdown content to write.
        filename: Target filename (will be sanitized).

    Returns:
        The Path of the written file.

    Raises:
        ReportWriteError: If the path is outside REPORTS_DIR or filename is invalid.
    """
    safe_name = _validate_filename(filename)
    target = REPORTS_DIR / safe_name
    _ensure_within_reports_dir(target)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    logger.info("Report saved: %s", target)
    return target


def append_to_report(content: str, filename: str = "tactics_analysis.md") -> Path:
    """Append content to an existing report (or create if missing)."""
    safe_name = _validate_filename(filename)
    target = REPORTS_DIR / safe_name
    _ensure_within_reports_dir(target)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    separator = f"\n\n---\n*Appended on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    with target.open("a", encoding="utf-8") as f:
        f.write(separator + content)
    logger.info("Appended to report: %s", target)
    return target


def list_reports() -> list[Path]:
    """Return all .md files in the reports directory."""
    if not REPORTS_DIR.exists():
        return []
    return sorted(REPORTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)


def read_report(filename: str) -> str | None:
    """Read a report from the reports directory, or None if not found."""
    safe_name = _validate_filename(filename)
    target = REPORTS_DIR / safe_name
    _ensure_within_reports_dir(target)
    if target.exists():
        return target.read_text(encoding="utf-8")
    return None
