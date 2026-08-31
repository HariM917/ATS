"""
TalentFlow AI — High-Dimensional Embedding Service & In-Memory Cache
Uses sentence-transformers/all-mpnet-base-v2 (768D) with retry backoff and caching.
"""
import time
import hashlib
import logging
from typing import List, Optional
import numpy as np
import requests

from ..core.config import settings

logger = logging.getLogger(__name__)

# LRU / In-memory embedding cache
_EMBEDDING_CACHE = {}


def _get_cache_key(text: str) -> str:
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()


def get_embedding(text: str) -> Optional[np.ndarray]:
    """Generate 768-dimensional MPNet embedding with caching and exponential retry."""
    if not text or not text.strip():
        return np.zeros(768, dtype=np.float32)

    cache_key = _get_cache_key(text)
    if cache_key in _EMBEDDING_CACHE:
        return _EMBEDDING_CACHE[cache_key]

    token = settings.ai.hf_token
    if not token:
        # Fallback to deterministic TF-IDF / pseudo-embedding if token is not set
        return _fallback_pseudo_embedding(text)

    api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.ai.embedding_model}"
    headers = {"Authorization": f"Bearer {token}"}

    for attempt in range(3):
        try:
            resp = requests.post(api_url, headers=headers, json={"inputs": text[:2000]}, timeout=10)
            if resp.status_code == 200:
                vec = np.array(resp.json(), dtype=np.float32)
                # Normalize embedding
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                if len(_EMBEDDING_CACHE) < settings.ai.embedding_cache_max:
                    _EMBEDDING_CACHE[cache_key] = vec
                return vec
            elif resp.status_code == 503:
                time.sleep(2 ** attempt)
        except Exception as e:
            logger.debug(f"[EMBEDDING] Attempt {attempt+1} failed: {e}")
            time.sleep(1)

    return _fallback_pseudo_embedding(text)


def _fallback_pseudo_embedding(text: str) -> np.ndarray:
    """Deterministic hash-based dense vector for offline/testing development."""
    vec = np.zeros(768, dtype=np.float32)
    words = text.lower().split()
    for i, word in enumerate(words[:768]):
        val = sum(ord(c) for c in word) % 100 / 100.0
        vec[i % 768] += val
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute cosine similarity between two unit vectors."""
    if v1 is None or v2 is None or len(v1) == 0 or len(v2) == 0:
        return 0.0
    dot = np.dot(v1, v2)
    return float(np.clip(dot, 0.0, 1.0))
