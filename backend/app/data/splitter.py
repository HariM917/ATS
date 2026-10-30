"""
TalentFlow AI — Data Splitter
================================
Deterministic train / validation / test split with leakage prevention.

Design rules:
  - Fixed random seed (42) for full reproducibility
  - A resume must NOT appear in more than one split
  - Near-duplicate clusters are assigned to the same split to prevent leakage
  - The test set is frozen — treated as unseen production data
  - Group-aware splitting when an ID or duplicate cluster column is available

Split ratios:
  - Train      : 70%
  - Validation : 15%
  - Test        : 15%

IMPORTANT: This module is TRAINING INFRASTRUCTURE only.
It must never be imported by the production application at runtime.
"""

import logging
from typing import Tuple, Optional, Dict, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataSplitter:
    """
    Deterministic, leakage-safe dataset splitter.

    Splitting strategy:
      1. If a group/ID column or cluster column exists, group records.
      2. Stratify by label column to maintain balanced class representation.
      3. Split at group/cluster level, not individual record level, to eliminate leakage.
      4. Test set is assigned first (highest priority to be held-out).
    """

    def __init__(
        self,
        text_column: str,
        label_column: str,
        id_column: Optional[str] = None,
        group_column: Optional[str] = None,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42,
    ) -> None:
        if not abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6:
            raise ValueError(
                f"Ratios must sum to 1.0, got {train_ratio + val_ratio + test_ratio}"
            )

        self.text_column = text_column
        self.label_column = label_column
        self.id_column = id_column
        self.group_column = group_column
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

        self._split_summary: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def split(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split the dataset into train, validation, and test sets.

        Returns:
            (train_df, val_df, test_df)
        """
        if self.label_column not in df.columns:
            raise ValueError(
                f"Label column '{self.label_column}' not found. "
                f"Available: {list(df.columns)}"
            )

        logger.info(
            f"[SPLITTER] Splitting {len(df):,} records "
            f"(train={self.train_ratio}, val={self.val_ratio}, test={self.test_ratio}, "
            f"seed={self.seed})"
        )

        rng = np.random.default_rng(self.seed)
        out = df.copy().reset_index(drop=True)

        # Determine grouping unit
        if self.group_column and self.group_column in df.columns:
            split_col = self.group_column
            logger.info(f"[SPLITTER] Splitting at cluster group level: '{split_col}'")
        elif self.id_column and self.id_column in df.columns:
            split_col = self.id_column
            logger.info(f"[SPLITTER] Splitting at ID group level: '{split_col}'")
        else:
            out["_synthetic_id"] = np.arange(len(out))
            split_col = "_synthetic_id"
            logger.info("[SPLITTER] No ID/group column; splitting at record level")

        # Get unique groups and their dominant labels
        groups = (
            out.groupby(split_col)[self.label_column]
            .agg(lambda x: x.mode().iloc[0] if len(x) > 0 else "unknown")
            .reset_index()
        )
        groups.columns = [split_col, "_dominant_label"]

        # Stratified split at group level
        train_groups, val_groups, test_groups = self._stratified_split_groups(
            groups, "_dominant_label", rng
        )

        # Assign split labels
        out["_split"] = "train"
        out.loc[out[split_col].isin(list(val_groups)), "_split"] = "val"
        out.loc[out[split_col].isin(list(test_groups)), "_split"] = "test"

        if "_synthetic_id" in out.columns:
            out = out.drop(columns=["_synthetic_id"])

        train_df = out[out["_split"] == "train"].copy()
        val_df = out[out["_split"] == "val"].copy()
        test_df = out[out["_split"] == "test"].copy()

        self._split_summary = {
            "total": len(out),
            "train": len(train_df),
            "val": len(val_df),
            "test": len(test_df),
            "train_pct": round(len(train_df) / len(out) * 100, 1),
            "val_pct": round(len(val_df) / len(out) * 100, 1),
            "test_pct": round(len(test_df) / len(out) * 100, 1),
            "seed": self.seed,
        }

        logger.info(
            f"[SPLITTER] Split complete: "
            f"train={len(train_df):,} ({self._split_summary['train_pct']}%), "
            f"val={len(val_df):,} ({self._split_summary['val_pct']}%), "
            f"test={len(test_df):,} ({self._split_summary['test_pct']}%)"
        )

        return train_df, val_df, test_df  # type: ignore

    def get_summary(self) -> Dict[str, Any]:
        """Return split statistics from the last call to split()."""
        return self._split_summary

    def verify_no_leakage(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
    ) -> Dict[str, int]:
        """
        Verify that no record or identical text appears in more than one split.
        """
        def get_ids(df_: pd.DataFrame) -> set:
            if self.id_column and self.id_column in df_.columns:
                return set(df_[self.id_column].astype(str).tolist())
            import hashlib
            return {
                hashlib.md5(" ".join(str(t).lower().split()).encode()).hexdigest()
                for t in df_[self.text_column].fillna("").tolist()
            }

        train_ids = get_ids(train_df)
        val_ids = get_ids(val_df)
        test_ids = get_ids(test_df)

        train_val_leak = len(train_ids & val_ids)
        train_test_leak = len(train_ids & test_ids)
        val_test_leak = len(val_ids & test_ids)

        leaks = {
            "train_val_overlap": train_val_leak,
            "train_test_overlap": train_test_leak,
            "val_test_overlap": val_test_leak,
        }

        if any(leaks.values()):
            logger.error(f"[SPLITTER] DATA LEAKAGE DETECTED: {leaks}")
        else:
            logger.info("[SPLITTER] Leakage check passed: 0 overlap between train/val/test splits")

        return leaks

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _stratified_split_groups(
        self,
        groups: pd.DataFrame,
        label_col: str,
        rng: np.random.Generator,
    ) -> Tuple[set, set, set]:
        id_col = groups.columns[0]
        train_ids, val_ids, test_ids = set(), set(), set()

        for label in groups[label_col].unique():
            label_groups = groups[groups[label_col] == label][id_col].tolist()
            n = len(label_groups)
            if n == 0:
                continue

            shuffled = rng.permutation(label_groups).tolist()

            n_test = max(1, round(n * self.test_ratio))
            n_val = max(1, round(n * self.val_ratio)) if n > 2 else 0
            n_train = n - n_test - n_val

            test_ids.update(shuffled[:n_test])
            val_ids.update(shuffled[n_test: n_test + n_val])
            train_ids.update(shuffled[n_test + n_val:])

        return train_ids, val_ids, test_ids
