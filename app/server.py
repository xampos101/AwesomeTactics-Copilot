"""HTTP API + embeddable widget for the tactics RAG copilot.

Run locally:
  uvicorn app.server:app --reload --port 8000

Then embed on any website by adding:
  <script src="http://localhost:8000/widget.js"
          data-api-base="http://localhost:8000"
          data-title="Tactics Copilot"></script>
"""

from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response

from app.config import ProviderConfig, get_providers
from ingestion.build_index import build_index
from rag.pipeline import run_query

ROOT = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(ROOT, "web", "static")

app = FastAPI(title="Agentic Tactics Copilot API", version="0.1.0")

allowed_origins = [
    o.strip()
    for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _pick_provider(provider_name: str | None) -> ProviderConfig:
    providers = get_providers()
    if not providers:
        # Fall back to an OpenAI-compatible local endpoint (Ollama/Nebula).
        return ProviderConfig(
            name="Manual (llama3)",
            api_base=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
            model=os.getenv("LLM_MODEL", "llama3"),
            api_key=os.getenv("LLM_API_KEY", "no-key"),
        )
    if not provider_name:
        return providers[0]
    match = next((p for p in providers if p.name == provider_name), None)
    if not match:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider '{provider_name}'. Available: {[p.name for p in providers]}",
        )
    return match


@app.on_event("startup")
def _startup() -> None:
    # Build Chroma from GitHub only when the local index is missing.
    # Existing data/chroma_db is reused; no git clone required.
    try:
        build_index(force_rebuild=False)
    except Exception:
        pass


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True}


@app.get("/widget.js")
def widget_js() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "widget.js"), media_type="application/javascript")


@app.get("/widget.css")
def widget_css() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "widget.css"), media_type="text/css")


@app.post("/api/chat")
async def chat(
    payload: dict[str, Any],
    request: Request,
    mode: Literal["recommend", "critique", "compare"] = "recommend",
    top_k: int = Query(8, ge=3, le=15),
    category: str | None = None,
    provider: str | None = None,
) -> JSONResponse:
    user_query = str(payload.get("query") or "").strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Missing 'query' in JSON body.")

    prov = _pick_provider(provider)
    result = run_query(
        user_query=user_query,
        mode=mode,
        provider=prov,
        n_results=top_k,
        category_filter=category,
    )
    if "error" in result:
        msg = str(result["error"])
        status = 500
        if "Connection error" in msg or "ConnectError" in msg or "ECONNREFUSED" in msg:
            status = 502
            msg = (
                msg
                + " (LLM provider unreachable. If you're using Ollama/Nebula locally, "
                + "ensure it's running and `LLM_API_BASE` / `NEBULA_API_BASE` is correct.)"
            )
        raise HTTPException(status_code=status, detail=msg)

    # Include request id-ish information for debugging if present.
    result["request"] = {
        "mode": mode,
        "top_k": top_k,
        "category": category,
        "provider": prov.name,
        "origin": request.headers.get("origin"),
    }
    return JSONResponse(result)


@app.get("/api/providers")
def list_providers() -> Response:
    providers = get_providers()
    if not providers:
        return JSONResponse({"providers": []})
    return JSONResponse(
        {
            "providers": [
                {"name": p.name, "model": p.model, "api_base": p.api_base, "commercial": p.is_commercial}
                for p in providers
            ]
        }
    )

