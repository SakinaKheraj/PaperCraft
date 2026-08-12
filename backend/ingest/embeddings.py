"""OpenAI embedding generation for document chunks."""

from __future__ import annotations

from openai import OpenAI
import httpx

from app.config import settings

EMBED_BATCH_SIZE = 100


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


import time
from concurrent.futures import ThreadPoolExecutor


def _embed_single_gemini_text(
    http_client: httpx.Client,
    api_key: str,
    text: str,
    expected_dims: int,
) -> list[float]:
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "outputDimensionality": expected_dims,
        "content": {"parts": [{"text": text}]},
    }
    endpoints = [
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent",
    ]

    last_err_text = ""
    for attempt in range(6):
        for url in endpoints:
            resp = http_client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                values = resp.json().get("embedding", {}).get("values", [])
                if len(values) < expected_dims:
                    values = values + [0.0] * (expected_dims - len(values))
                elif len(values) > expected_dims:
                    values = values[:expected_dims]
                return values
            elif resp.status_code == 429:
                time.sleep(3.0 * (attempt + 1))
                break
            else:
                last_err_text = f"HTTP {resp.status_code}: {resp.text}"

    raise RuntimeError(f"Gemini embedding failed on all endpoints: {last_err_text}")


def _embed_gemini_texts(texts: list[str], expected_dims: int) -> list[list[float]]:
    api_key = settings.openai_api_key
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    vectors: list[list[float]] = []
    batch_size = 100
    models = [
        "models/gemini-embedding-2",
        "models/gemini-embedding-001",
        "models/gemini-embedding-2-preview",
    ]

    with httpx.Client(timeout=60.0) as http_client:
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            success = False

            for attempt in range(12):
                for model_candidate in models:
                    url = f"https://generativelanguage.googleapis.com/v1beta/{model_candidate}:batchEmbedContents"
                    payload = {
                        "requests": [
                            {
                                "model": model_candidate,
                                "content": {"parts": [{"text": text}]},
                                "outputDimensionality": expected_dims,
                            }
                            for text in batch
                        ]
                    }
                    resp = http_client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        batch_embeddings = data.get("embeddings", [])
                        for item in batch_embeddings:
                            vals = item.get("values", [])
                            if len(vals) < expected_dims:
                                vals = vals + [0.0] * (expected_dims - len(vals))
                            elif len(vals) > expected_dims:
                                vals = vals[:expected_dims]
                            vectors.append(vals)
                        success = True
                        break
                    elif resp.status_code == 429:
                        continue

                if success:
                    break

                time.sleep(10.0 * (attempt + 1))

            if not success:
                raise RuntimeError(
                    f"Gemini embedding batch failed for range {start}:{start + batch_size} after retries."
                )

            time.sleep(1.0)

    if len(vectors) != len(texts):
        raise ValueError(
            f"Expected {len(texts)} embeddings, but generated {len(vectors)}."
        )

    return vectors


def embed_texts(texts: list[str], *, batch_size: int = EMBED_BATCH_SIZE) -> list[list[float]]:
    if not texts:
        return []

    expected_dims = settings.openai_embedding_dimensions

    if _is_gemini():
        return _embed_gemini_texts(texts, expected_dims)

    vectors: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        response = _client().embeddings.create(
            input=batch,
            model=settings.openai_embedding_model,
            dimensions=expected_dims,
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        for item in ordered:
            embedding = item.embedding
            if len(embedding) != expected_dims:
                raise ValueError(
                    f"Expected embedding dimension {expected_dims}, got {len(embedding)}"
                )
            vectors.append(embedding)

    return vectors
