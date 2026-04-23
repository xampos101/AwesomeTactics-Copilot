"""Central configuration for the Agentic Tactics Copilot."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
AADT_REPO_DIR = DATA_DIR / "aadt-repo"
AADT_POSTS_DIR = AADT_REPO_DIR / "docs" / "_posts"
AADT_CATEGORIES_DIR = AADT_REPO_DIR / "docs" / "categories"
CHROMA_DIR = DATA_DIR / "chroma_db"
REPORTS_DIR = ROOT_DIR / "reports"
EVAL_DIR = ROOT_DIR / "evaluation"

AADT_BASE_URL = "https://s2group.cs.vu.nl/AwesomeAndDarkTactics"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class ProviderConfig(BaseModel):
    """LLM provider connection settings."""

    name: str
    api_base: str
    model: str
    api_key: str = ""
    is_commercial: bool = False


def get_providers() -> list[ProviderConfig]:
    """Return configured LLM providers from environment variables."""
    providers: list[ProviderConfig] = []

    nebula_base = os.getenv("NEBULA_API_BASE", "http://localhost:11434/v1")
    for i in (1, 2):
        model = os.getenv(f"NEBULA_MODEL_{i}")
        if model:
            providers.append(
                ProviderConfig(
                    name=f"Nebula ({model})",
                    api_base=nebula_base,
                    model=model,
                    api_key=os.getenv("NEBULA_API_KEY", "nebula"),
                )
            )

    openai_key = os.getenv("OPENAI_API_KEY", "")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if openai_key and openai_key != "sk-your-key-here":
        providers.append(
            ProviderConfig(
                name=f"OpenAI ({openai_model})",
                api_base="https://api.openai.com/v1",
                model=openai_model,
                api_key=openai_key,
                is_commercial=True,
            )
        )

    return providers


# --- Canonical JSON response schemas ---


class TacticReference(BaseModel):
    """A single tactic citation from the AADT catalog."""

    tactic_name: str
    category: str
    tactic_type: str = Field(description="'Awesome Tactic' or 'Dark Tactic'")
    description: str
    source: str = ""
    source_doi: str = ""
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)


class RecommendResponse(BaseModel):
    """Canonical output for recommend mode."""

    mode: str = "recommend"
    query: str
    summary: str
    tactics: list[TacticReference]
    dark_tactic_risks: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    grounding_note: str = ""


class CritiqueResponse(BaseModel):
    """Canonical output for critique mode."""

    mode: str = "critique"
    query: str
    verdict: str = Field(description="aligned | mixed | dark_tactic_risk")
    verdict_label: str
    analysis: str
    matched_tactics: list[TacticReference]
    risks: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    grounding_note: str = ""


class CompareResponse(BaseModel):
    """Canonical output for compare mode."""

    mode: str = "compare"
    query: str
    subjects: list[str]
    comparison_table: dict
    key_tradeoffs: list[str]
    recommendation: str
    sources: list[str] = Field(default_factory=list)
    grounding_note: str = ""
