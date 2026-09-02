"""
TalentFlow AI — FAISS Vector Index Management
Abstraction over FAISS for build, search, persist, and reload operations.
Used by RAG and matching engine for semantic search.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

try:
    import faiss
    _HAS_FAISS = True
except ImportError:
    _HAS_FAISS = False
    logger.warning("[VECTOR_STORE] FAISS not available. Falling back to brute-force numpy search.")


class VectorStore:
    """In-memory vector index with FAISS backend and numpy fallback."""

    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.index = None
        self.vectors: List[np.ndarray] = []
        self.metadata: List[Dict[str, Any]] = []

    @property
    def size(self) -> int:
        return len(self.vectors)

    def add(self, vector: np.ndarray, meta: Dict[str, Any] = None) -> int:
        """Add a vector with optional metadata. Returns the index position."""
        if vector is None or len(vector) == 0:
            return -1
        vec = np.array(vector, dtype=np.float32).reshape(1, -1)
        self.vectors.append(vec.flatten())
        self.metadata.append(meta or {})
        # Invalidate FAISS index so it rebuilds on next search
        self.index = None
        return len(self.vectors) - 1

    def build_index(self) -> None:
        """Build or rebuild the FAISS index from stored vectors."""
        if not self.vectors:
            return
        arr = np.array(self.vectors, dtype=np.float32)
        if _HAS_FAISS:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.index.add(arr)
            logger.info(f"[VECTOR_STORE] FAISS index built with {len(self.vectors)} vectors")
        else:
            # Store array for numpy fallback
            self._np_matrix = arr
            logger.info(f"[VECTOR_STORE] NumPy index built with {len(self.vectors)} vectors")

    def search(self, query_vector: np.ndarray, top_k: int = 5, min_score: float = 0.0) -> List[Tuple[int, float, Dict[str, Any]]]:
        """Search for nearest vectors. Returns list of (index, score, metadata) tuples."""
        if not self.vectors:
            return []

        if self.index is None:
            self.build_index()

        q_vec = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        top_k = min(top_k, len(self.vectors))

        if _HAS_FAISS and self.index is not None:
            distances, indices = self.index.search(q_vec, top_k)
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.metadata) and dist >= min_score:
                    results.append((int(idx), float(dist), self.metadata[idx]))
            return results
        else:
            # Numpy fallback: cosine similarity
            scores = np.dot(self._np_matrix, q_vec.T).flatten()
            top_indices = np.argsort(scores)[::-1][:top_k]
            results = []
            for idx in top_indices:
                score = float(scores[idx])
                if score >= min_score:
                    results.append((int(idx), score, self.metadata[idx]))
            return results

    def clear(self) -> None:
        """Clear all vectors and metadata."""
        self.vectors = []
        self.metadata = []
        self.index = None

    def save(self, path: str) -> None:
        """Save vectors and metadata to disk."""
        import json
        np.save(f"{path}.npy", np.array(self.vectors, dtype=np.float32))
        with open(f"{path}.meta.json", "w") as f:
            json.dump(self.metadata, f)
        logger.info(f"[VECTOR_STORE] Saved {len(self.vectors)} vectors to {path}")

    def load(self, path: str) -> bool:
        """Load vectors and metadata from disk. Returns True if successful."""
        import json
        try:
            arr = np.load(f"{path}.npy")
            with open(f"{path}.meta.json", "r") as f:
                meta = json.load(f)
            self.vectors = [arr[i] for i in range(len(arr))]
            self.metadata = meta
            self.build_index()
            logger.info(f"[VECTOR_STORE] Loaded {len(self.vectors)} vectors from {path}")
            return True
        except Exception as e:
            logger.warning(f"[VECTOR_STORE] Failed to load from {path}: {e}")
            return False
