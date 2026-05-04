"""RAG retrieval for DeepTraining TOEIC knowledge base."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("deeptraining.rag")


SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

OLLAMA_EMBEDDING_BASE_URL = os.getenv("OLLAMA_EMBEDDING_BASE_URL", "http://localhost:11434").rstrip("/")
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text:latest")

RAG_MATCH_COUNT = int(os.getenv("RAG_MATCH_COUNT", "4"))
RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.10"))
RAG_TIMEOUT_SECONDS = float(os.getenv("RAG_TIMEOUT_SECONDS", "120"))


class RagRetrievalError(RuntimeError):
    pass


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.8f}" for value in values) + "]"


def _supabase_headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Accept-Profile": "app",
        "Content-Profile": "app",
        "Content-Type": "application/json",
    }


async def _embedding_for_text(text: str) -> list[float]:
    endpoint = f"{OLLAMA_EMBEDDING_BASE_URL}/api/embeddings"
    payload = {
        "model": RAG_EMBEDDING_MODEL,
        "prompt": text,
    }

    async with httpx.AsyncClient(timeout=RAG_TIMEOUT_SECONDS) as client:
        response = await client.post(endpoint, json=payload)

    if response.status_code >= 400:
        raise RagRetrievalError(f"Ollama embedding returned HTTP {response.status_code}")

    data = response.json()
    embedding = data.get("embedding")

    if not embedding:
        raise RagRetrievalError("Ollama embedding returned an empty embedding")

    if len(embedding) != 768:
        raise RagRetrievalError(f"Unexpected embedding dimension: {len(embedding)}")

    return embedding


async def retrieve_knowledge_chunks(query: str) -> list[dict[str, Any]]:
    clean_query = query.strip()

    if not clean_query:
        return []

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("rag disabled: missing Supabase configuration")
        return []

    embedding = await _embedding_for_text(clean_query)

    payload = {
        "query_embedding": _vector_literal(embedding),
        "query_text": clean_query,
        "match_count": RAG_MATCH_COUNT,
        "similarity_threshold": RAG_SIMILARITY_THRESHOLD,
    }

    endpoint = f"{SUPABASE_URL}/rest/v1/rpc/match_knowledge_chunks_hybrid"

    async with httpx.AsyncClient(timeout=RAG_TIMEOUT_SECONDS) as client:
        response = await client.post(endpoint, json=payload, headers=_supabase_headers())

    if response.status_code >= 400:
        raise RagRetrievalError(f"Supabase RAG RPC returned HTTP {response.status_code}: {response.text}")

    data = response.json()

    if not isinstance(data, list):
        raise RagRetrievalError("Supabase RAG RPC returned an invalid payload")

    return data


def format_knowledge_context(chunks: list[dict[str, Any]]) -> str:
    formatted_chunks: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        content = (chunk.get("content") or "").strip()
        if not content:
            continue

        source = chunk.get("source_filename") or "source inconnue"
        page = chunk.get("page_number")
        final_score = chunk.get("final_score")
        keyword_rank = chunk.get("keyword_rank")

        page_label = f", page {page}" if page is not None else ""
        score_label = ""
        if final_score is not None:
            score_label = f", final_score={final_score}"

        formatted_chunks.append(
            f"[Document {index} : {source}{page_label}{score_label}, keyword_rank={keyword_rank}]\n"
            f"{content[:1800]}"
        )

    return "\n\n---\n\n".join(formatted_chunks)


async def retrieve_knowledge_context(query: str) -> str:
    try:
        chunks = await retrieve_knowledge_chunks(query)
        context = format_knowledge_context(chunks)
        logger.info("rag retrieval ok query_chars=%s chunks=%s context_chars=%s", len(query), len(chunks), len(context))
        return context
    except Exception as exc:
        logger.warning("rag retrieval failed: %s", exc)
        return ""
