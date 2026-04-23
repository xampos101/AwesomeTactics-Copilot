"""Build a Chroma vector index from the loaded AADT tactics."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.config import CHROMA_DIR, DATA_DIR
from ingestion.load_aadt import load_categories, load_tactics

COLLECTION_NAME = "aadt_tactics"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def build_index(force_rebuild: bool = False) -> chromadb.Collection:
    """Create or return the Chroma collection over AADT tactics."""
    if force_rebuild and CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing and not force_rebuild:
        return client.get_collection(name=COLLECTION_NAME, embedding_function=ef)

    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    categories = load_categories()
    tactics = load_tactics()

    if not tactics:
        raise RuntimeError("No tactics found. Did you clone the AADT repo?")

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for i, t in enumerate(tactics):
        cat_info = categories.get(t["category"], {})
        doc_id = f"tactic-{i:03d}-{t['title'][:40].replace(' ', '_')}"

        metadata = {
            "title": t["title"],
            "category": t["category"],
            "category_type": cat_info.get("type", ""),
            "tactic_type": t["tactic_type"],
            "tags": json.dumps(t["tags"]),
            "source": t["source"],
            "source_doi": t["source_doi"],
            "url": t["url"],
            "intent": t["intent"],
            "target_qa": t["target_qa"],
        }

        ids.append(doc_id)
        documents.append(t["full_text"])
        metadatas.append(metadata)

    batch_size = 100
    for start in range(0, len(ids), batch_size):
        end = min(start + batch_size, len(ids))
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

    manifest = {
        "total_tactics": len(tactics),
        "categories": list(categories.keys()),
        "embedding_model": EMBEDDING_MODEL,
    }
    (DATA_DIR / "index_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Indexed {len(tactics)} tactics into Chroma ({CHROMA_DIR})")
    return collection


def get_collection() -> chromadb.Collection:
    """Return the existing Chroma collection (build if missing)."""
    if not CHROMA_DIR.exists() or not any(CHROMA_DIR.iterdir()):
        return build_index()
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(name=COLLECTION_NAME, embedding_function=ef)


if __name__ == "__main__":
    col = build_index(force_rebuild=True)
    print(f"Collection has {col.count()} documents")

    results = col.query(query_texts=["energy efficient ML training"], n_results=3)
    print("\nSample query: 'energy efficient ML training'")
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"  [{meta['tactic_type']}] {meta['title']} ({meta['category']})")
