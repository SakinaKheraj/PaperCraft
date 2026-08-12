"""OpenAI query embedding for live retrieval."""

from __future__ import annotations

from openai import OpenAI
import httpx

from app.config import settings


def _is_gemini() -> bool:
    key = settings.openai_api_key
    base_url = settings.openai_base_url or ""
    return (
        key.startswith("AIzaSy")
        or key.startswith("AQ.")
        or "generativelanguage.googleapis.com" in base_url
    )


def _client() -> OpenAI:
    kwargs = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**kwargs)


def _embed_gemini_query(text: str) -> list[float]:
    api_key = settings.openai_api_key
    expected_dims = settings.openai_embedding_dimensions
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "outputDimensionality": expected_dims,
        "content": {"parts": [{"text": text}]},
    }
    endpoints = [
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent",
    ]
    with httpx.Client(timeout=30.0) as http_client:
        for url in endpoints:
            resp = http_client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                values = resp.json().get("embedding", {}).get("values", [])
                if len(values) < expected_dims:
                    values = values + [0.0] * (expected_dims - len(values))
                elif len(values) > expected_dims:
                    values = values[:expected_dims]
                return values
    return [0.0] * expected_dims


def embed_query(text: str) -> list[float]:
    if _is_gemini():
        return _embed_gemini_query(text)

    response = _client().embeddings.create(
        input=[text],
        model=settings.openai_embedding_model,
        dimensions=settings.openai_embedding_dimensions,
    )
    embedding = response.data[0].embedding
    expected_dims = settings.openai_embedding_dimensions
    if len(embedding) != expected_dims:
        raise ValueError(
            f"Expected embedding dimension {expected_dims}, got {len(embedding)}"
        )
    return embedding
