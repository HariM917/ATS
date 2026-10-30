"""
TalentFlow AI — Duplicate Detector
=====================================
Detects exact and near-duplicate records in the resume dataset.

Approach:
  - Exact duplicates: MD5 hash of lowercased, whitespace-collapsed text
  - Near-duplicates: Cosine similarity on TF-IDF sparse vectors (threshold >= 0.95)
  - Duplicate audit report written to data/reports/duplicates.csv

Design rules:
  - Records are FLAGGED with recommended actions, not silently deleted
  - The raw file is NEVER mutated
  - Detailed similarity scores and source record references are recorded

IMPORTANT: This module is TRAINING INFRASTRUCTURE only.
It must never be imported by the production application at runtime.
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class Deduplicator:
    """
    Detect exact and near-duplicate records.

    Args:
        text_column:        Column containing resume text.
        id_column:          Column containing unique record ID (optional).
        near_dup_threshold: Cosine similarity above which two records are
                            considered near-duplicates. Default 0.95.
        near_dup_max_features: TF-IDF vocabulary size cap for memory efficiency.
        skip_near_dup:      If True, skip the near-dup detection step.
    """

    def __init__(
        self,
        text_column: str,
        id_column: Optional[str] = None,
        near_dup_threshold: float = 0.95,
        near_dup_max_features: int = 10_000,
        skip_near_dup: bool = False,
    ) -> None:
        self.text_column = text_column
        self.id_column = id_column
        self.near_dup_threshold = near_dup_threshold
        self.near_dup_max_features = near_dup_max_features
        self.skip_near_dup = skip_near_dup

        self._report: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, df: pd.DataFrame, show_progress: bool = False) -> pd.DataFrame:
        """
        Run exact + near-duplicate detection.

        Adds columns:
          _dup_hash          : MD5 hash of normalized text
          _exact_dup         : True if this row is an exact duplicate of a prior row
          _exact_dup_of      : ID of the first occurrence
          _near_dup          : True if near-duplicate of a prior row
          _near_dup_of       : ID of the near-duplicate canonical row
          _near_dup_score    : Cosine similarity score (0.0 to 1.0)
          _dup_action        : 'keep' | 'exact_remove' | 'near_dup_flag'

        Returns a copy of df with the above columns added.
        """
        if self.text_column not in df.columns:
            raise ValueError(
                f"Text column '{self.text_column}' not found. "
                f"Available: {list(df.columns)}"
            )

        out = df.copy().reset_index(drop=True)
        self._report = []

        # --- Exact Duplicate Detection ---
        logger.info("[DEDUP] Running exact duplicate detection...")
        out = self._detect_exact(out)

        exact_count = int(out["_exact_dup"].sum())  # type: ignore
        logger.info(f"[DEDUP] Exact duplicates detected: {exact_count:,}")

        # --- Near-Duplicate Detection ---
        if self.skip_near_dup:
            out["_near_dup"] = False
            out["_near_dup_of"] = None
            out["_near_dup_score"] = 0.0
            logger.info("[DEDUP] Near-duplicate detection skipped (skip_near_dup=True)")
        else:
            logger.info(
                f"[DEDUP] Running near-duplicate detection "
                f"(threshold={self.near_dup_threshold})..."
            )
            # Only check non-exact-dup rows with non-empty text to save time
            valid_mask = (~out["_exact_dup"]) & (out[self.text_column].fillna("").str.strip() != "")
            valid_indices = out.index[valid_mask].tolist()
            out = self._detect_near_dup(out, valid_indices, show_progress=show_progress)
            near_count = int(out["_near_dup"].sum())  # type: ignore
            logger.info(f"[DEDUP] Near-duplicates detected: {near_count:,}")

        # --- Assign Recommended Actions ---
        out["_dup_action"] = "keep"
        out.loc[out["_exact_dup"], "_dup_action"] = "exact_remove"
        out.loc[out["_near_dup"] & ~out["_exact_dup"], "_dup_action"] = "near_dup_flag"

        # Build report rows
        for _, row in out[out["_dup_action"] != "keep"].iterrows():
            rid = str(row[self.id_column]) if self.id_column else str(row.name)
            action = "REMOVE" if row["_exact_dup"] else "REVIEW"  # type: ignore
            self._report.append(
                {
                    "resume_id": rid,
                    "duplicate_of": row.get("_exact_dup_of") or row.get("_near_dup_of"),
                    "duplicate_type": "EXACT_DUPLICATE" if row["_exact_dup"] else "NEAR_DUPLICATE",  # type: ignore
                    "similarity": round(float(row.get("_near_dup_score", 1.0 if row["_exact_dup"] else 0.0)), 4),  # type: ignore
                    "recommended_action": action,
                    "action": action,
                }
            )

        return out

    def get_report(self) -> pd.DataFrame:
        """Return the duplicate report as a DataFrame."""
        if not self._report:
            return pd.DataFrame(
                columns=["resume_id", "duplicate_of", "duplicate_type", "similarity", "recommended_action", "action"]
            )
        return pd.DataFrame(self._report)

    def summary(self, df_flagged: pd.DataFrame) -> Dict[str, int]:
        """Return a summary count dictionary."""
        return {
            "total_records": len(df_flagged),
            "exact_duplicates": int(df_flagged.get("_exact_dup", pd.Series([False])).sum()),  # type: ignore
            "near_duplicates": int(df_flagged.get("_near_dup", pd.Series([False])).sum()),  # type: ignore
            "clean_records": int((df_flagged["_dup_action"] == "keep").sum()),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_hash(self, text: str) -> str:
        """MD5 hash of lowercased, whitespace-collapsed text."""
        normalized = " ".join(str(text).lower().split())
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def _detect_exact(self, df: pd.DataFrame) -> pd.DataFrame:
        df["_dup_hash"] = df[self.text_column].apply(self._make_hash)
        df["_exact_dup"] = False
        df["_exact_dup_of"] = None

        seen: Dict[str, Any] = {}  # hash -> first occurrence ID
        for idx, row in df.iterrows():
            text_str = str(row[self.text_column]).strip()
            if not text_str or text_str == "nan":
                continue

            h = row["_dup_hash"]
            rid = str(row[self.id_column]) if self.id_column else str(idx)
            if h in seen:
                df.at[idx, "_exact_dup"] = True
                df.at[idx, "_exact_dup_of"] = seen[h]  # type: ignore
            else:
                seen[h] = rid  # type: ignore

        return df

    def _detect_near_dup(
        self, df: pd.DataFrame, candidate_indices: List[int], show_progress: bool = False
    ) -> pd.DataFrame:
        df["_near_dup"] = False
        df["_near_dup_of"] = None
        df["_near_dup_score"] = 0.0

        if len(candidate_indices) < 2:
            return df

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity as sk_cosine

            texts = df.loc[candidate_indices, self.text_column].fillna("").tolist()
            vectorizer = TfidfVectorizer(
                max_features=self.near_dup_max_features,
                sublinear_tf=True,
                strip_accents="unicode",
                stop_words="english",
            )
            tfidf_matrix = vectorizer.fit_transform(texts)

            n = len(candidate_indices)

            # For moderate n (<= 5,000), compute pairwise similarity matrix directly
            if n <= 5000:
                sim_matrix = sk_cosine(tfidf_matrix)
                np.fill_diagonal(sim_matrix, 0.0)

                for i in range(n):
                    # Only consider prior items (j < i) as the duplicate parent
                    row_prior_sims = sim_matrix[i, :i]
                    if len(row_prior_sims) > 0:
                        max_sim = float(row_prior_sims.max())
                        if max_sim >= self.near_dup_threshold:
                            dup_of_local = int(row_prior_sims.argmax())
                            dup_of_global = candidate_indices[dup_of_local]
                            dup_of_id = (
                                str(df.at[dup_of_global, self.id_column])
                                if self.id_column
                                else str(dup_of_global)
                            )
                            global_idx = candidate_indices[i]
                            df.at[global_idx, "_near_dup"] = True
                            df.at[global_idx, "_near_dup_of"] = dup_of_id
                            df.at[global_idx, "_near_dup_score"] = round(max_sim, 4)
            else:
                chunk_size = 500
                iterator = range(0, n, chunk_size)
                if show_progress:
                    try:
                        from tqdm import tqdm
                        iterator = tqdm(iterator, desc="Near-dup scanning", leave=False)
                    except ImportError:
                        pass

                for i in iterator:
                    chunk_end = min(i + chunk_size, n)
                    chunk_matrix = tfidf_matrix[i:chunk_end]

                    # Prior chunks
                    if i > 0:
                        sims = sk_cosine(chunk_matrix, tfidf_matrix[:i])
                        for ci in range(sims.shape[0]):
                            row_sims = sims[ci]
                            global_idx = candidate_indices[i + ci]
                            max_sim = float(row_sims.max())
                            if max_sim >= self.near_dup_threshold:
                                dup_of_local = int(row_sims.argmax())
                                dup_of_global = candidate_indices[dup_of_local]
                                dup_of_id = (
                                    str(df.at[dup_of_global, self.id_column])
                                    if self.id_column
                                    else str(dup_of_global)
                                )
                                df.at[global_idx, "_near_dup"] = True
                                df.at[global_idx, "_near_dup_of"] = dup_of_id
                                df.at[global_idx, "_near_dup_score"] = round(max_sim, 4)

                    # Within current chunk
                    intra_sims = sk_cosine(chunk_matrix)
                    for ci in range(intra_sims.shape[0]):
                        global_idx = candidate_indices[i + ci]
                        # Only check items before ci in this chunk if not already matched
                        if not df.at[global_idx, "_near_dup"] and ci > 0:
                            intra_row = intra_sims[ci, :ci]
                            max_sim = float(intra_row.max())
                            if max_sim >= self.near_dup_threshold:
                                dup_of_local = i + int(intra_row.argmax())
                                dup_of_global = candidate_indices[dup_of_local]
                                dup_of_id = (
                                    str(df.at[dup_of_global, self.id_column])
                                    if self.id_column
                                    else str(dup_of_global)
                                )
                                df.at[global_idx, "_near_dup"] = True
                                df.at[global_idx, "_near_dup_of"] = dup_of_id
                                df.at[global_idx, "_near_dup_score"] = round(max_sim, 4)

        except ImportError:
            logger.warning(
                "[DEDUP] scikit-learn not available — skipping near-duplicate detection."
            )

        return df
