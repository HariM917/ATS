"""
TalentFlow AI — Data Validator
=================================
Schema validation, missing value detection, and record quality checks.

Validates:
  - Required columns are present
  - No critical columns exceed null thresholds
  - Text length meets minimum thresholds
  - Label column has expected distribution
  - Duplicate IDs
  - Suspicious records (all-whitespace, HTML-only, symbol-only)

IMPORTANT: This module is TRAINING INFRASTRUCTURE only.
It must never be imported by the production application at runtime.
"""

import logging
import re
from typing import Dict, Any, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Pattern that matches text that is likely extraction garbage
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_ONLY_SPECIAL_CHARS = re.compile(r"^[\W\d_]+$")


class DataValidator:
    """
    Validate dataset quality before processing.

    Args:
        text_column:    Column containing resume text.
        label_column:   Column containing category/role labels.
        id_column:      Optional unique ID column.
        min_text_chars: Minimum acceptable text length.
        min_text_words: Minimum acceptable word count.
        min_label_count:Minimum samples per category (warn if below).
        max_null_pct:   Maximum acceptable null percentage per column (0–100).
    """

    def __init__(
        self,
        text_column: str,
        label_column: str,
        id_column: Optional[str] = None,
        min_text_chars: int = 100,
        min_text_words: int = 20,
        min_label_count: int = 5,
        max_null_pct: float = 10.0,
    ) -> None:
        self.text_column = text_column
        self.label_column = label_column
        self.id_column = id_column
        self.min_text_chars = min_text_chars
        self.min_text_words = min_text_words
        self.min_label_count = min_label_count
        self.max_null_pct = max_null_pct

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run all validation checks.

        Returns:
            {
              "passed": bool,
              "errors":   [str],   # blocking issues
              "warnings": [str],   # non-blocking observations
              "stats":    {...},   # summary statistics
            }
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Column presence
        self._check_columns(df, errors)
        if errors:
            return self._result(False, errors, warnings, {})

        # 2. Null checks
        self._check_nulls(df, errors, warnings)

        # 3. Text length & quality
        stats = self._check_text_quality(df, warnings)

        # 4. Label distribution
        self._check_label_distribution(df, warnings)

        # 5. Duplicate ID check
        if self.id_column:
            self._check_duplicate_ids(df, warnings)

        # 6. Suspicious records
        susp = self._check_suspicious_records(df, warnings)
        stats["suspicious_records"] = susp

        passed = len(errors) == 0
        return self._result(passed, errors, warnings, stats)

    # ------------------------------------------------------------------
    # Internal check methods
    # ------------------------------------------------------------------

    def _check_columns(self, df: pd.DataFrame, errors: List[str]) -> None:
        required = [self.text_column, self.label_column]
        for col in required:
            if col not in df.columns:
                errors.append(
                    f"Required column '{col}' not found. "
                    f"Available columns: {list(df.columns)}"
                )
        if self.id_column and self.id_column not in df.columns:
            errors.append(
                f"ID column '{self.id_column}' specified but not found. "
                f"Available: {list(df.columns)}"
            )

    def _check_nulls(
        self, df: pd.DataFrame, errors: List[str], warnings: List[str]
    ) -> None:
        for col in [self.text_column, self.label_column]:
            null_count = df[col].isna().sum()
            null_pct = null_count / len(df) * 100
            if null_pct > self.max_null_pct:
                errors.append(
                    f"Column '{col}' has {null_pct:.1f}% null values "
                    f"(threshold: {self.max_null_pct}%)"
                )
            elif null_count > 0:
                warnings.append(
                    f"Column '{col}' has {null_count:,} null values ({null_pct:.2f}%)"
                )

    def _check_text_quality(
        self, df: pd.DataFrame, warnings: List[str]
    ) -> Dict[str, Any]:
        texts = df[self.text_column].fillna("").astype(str)
        lengths = texts.str.len()
        words = texts.str.split().apply(len)

        short_chars = (lengths < self.min_text_chars).sum()  # type: ignore
        short_words = (words < self.min_text_words).sum()  # type: ignore
        empty = (lengths == 0).sum()  # type: ignore

        if empty > 0:
            warnings.append(f"{empty:,} records have empty text")
        if short_chars > 0:
            warnings.append(
                f"{short_chars:,} records have text shorter than {self.min_text_chars} chars"
            )
        if short_words > 0:
            warnings.append(
                f"{short_words:,} records have fewer than {self.min_text_words} words"
            )

        valid_lengths = lengths[lengths > 0]
        valid_words = words[words > 0]

        return {
            "total_records": len(df),
            "empty_text": empty,
            "short_char_records": short_chars,
            "short_word_records": short_words,
            "min_length": valid_lengths.min() if len(valid_lengths) > 0 else 0,  # type: ignore
            "max_length": valid_lengths.max() if len(valid_lengths) > 0 else 0,  # type: ignore
            "mean_length": round(valid_lengths.mean(), 1) if len(valid_lengths) > 0 else 0,  # type: ignore
            "median_length": round(valid_lengths.median(), 1) if len(valid_lengths) > 0 else 0,  # type: ignore
            "min_words": valid_words.min() if len(valid_words) > 0 else 0,  # type: ignore
            "max_words": valid_words.max() if len(valid_words) > 0 else 0,  # type: ignore
            "mean_words": round(valid_words.mean(), 1) if len(valid_words) > 0 else 0,  # type: ignore
        }

    def _check_label_distribution(
        self, df: pd.DataFrame, warnings: List[str]
    ) -> None:
        dist = df[self.label_column].value_counts()
        weak = dist[dist < self.min_label_count]
        if len(weak) > 0:
            warnings.append(
                f"{len(weak)} categories have fewer than "
                f"{self.min_label_count} samples: {list(weak.keys())[:10]}"  # type: ignore
            )

    def _check_duplicate_ids(
        self, df: pd.DataFrame, warnings: List[str]
    ) -> None:
        dup_count = df[self.id_column].duplicated().sum()
        if dup_count > 0:
            warnings.append(
                f"ID column '{self.id_column}' has {dup_count:,} duplicate values"
            )

    def _check_suspicious_records(
        self, df: pd.DataFrame, warnings: List[str]
    ) -> int:
        texts = df[self.text_column].fillna("").astype(str)

        # HTML-heavy text (likely unparsed HTML)
        html_heavy = texts.apply(
            lambda t: len(_HTML_TAG_PATTERN.findall(t)) > 10
        ).sum()

        # Only special characters / digits — likely garbage
        only_special = texts.apply(
            lambda t: bool(_ONLY_SPECIAL_CHARS.match(t.strip())) if t.strip() else False
        ).sum()

        total_suspicious = int(html_heavy.item() + only_special.item())
        if total_suspicious > 0:
            pct = round(total_suspicious / len(df) * 100, 2)
            warnings.append(
                f"{total_suspicious:,} records ({pct}%) appear suspicious: "
                f"{int(html_heavy.item())} HTML-heavy, {int(only_special.item())} symbol-only"
            )
        return total_suspicious

    @staticmethod
    def _result(
        passed: bool,
        errors: List[str],
        warnings: List[str],
        stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        logger.info(
            f"[VALIDATOR] passed={passed}, "
            f"errors={len(errors)}, warnings={len(warnings)}"
        )
        if errors:
            for e in errors:
                logger.error(f"[VALIDATOR] ERROR: {e}")
        for w in warnings:
            logger.warning(f"[VALIDATOR] WARNING: {w}")
        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "stats": stats,
        }
