"""
TalentFlow AI — Text Cleaner
==============================
Safe text preprocessing for resume data.

Design rules:
  - Preserve technical terminology (Python, C++, C#, Node.js, React.js, scikit-learn, PyTorch, etc.)
  - Preserve casing and structure of recognized terms
  - Do NOT over-aggressively strip or rewrite content
  - Clean Unicode, remove OCR/extraction artifacts, and normalize whitespace
  - Operate on a copy; never mutate the source DataFrame

IMPORTANT: This module is TRAINING INFRASTRUCTURE only.
It must never be imported by the production application at runtime.
"""

import re
import logging
import unicodedata
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Characters that are typically extraction artifacts from PDF/OCR
_ARTIFACT_PATTERNS = [
    # Repeated special chars (3+) that are not meaningful bullets or syntax
    (re.compile(r"[•·▪▸►▶◆★☆○●]{3,}"), " "),
    # Windows-style line endings
    (re.compile(r"\r\n"), "\n"),
    (re.compile(r"\r"), "\n"),
    # NUL bytes and non-printable control chars (except tab/newline)
    (re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"), ""),
    # Repeated dashes/underscores (separator lines in PDFs)
    (re.compile(r"[-_=]{5,}"), " "),
    # Excessive consecutive repeated non-word characters
    (re.compile(r"([~`!@$%^&*()+={}\[\]|\\:;\"'<>,.?/])\1{4,}"), r"\1"),
    # Repeated whitespace/newlines collapsed safely
    (re.compile(r"[ \t]{2,}"), " "),
    (re.compile(r"\n{3,}"), "\n\n"),
]

# Section headers that appear duplicated due to extraction artifacts
_DUPLICATE_HEADER_PATTERN = re.compile(
    r"(SKILLS|EXPERIENCE|EDUCATION|PROJECTS|SUMMARY|OBJECTIVE|CERTIFICATIONS)"
    r"(\s*[:\-•]?\s*\1)+",
    re.IGNORECASE,
)

# PII regex patterns for audit/sanitization
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
PHONE_PATTERN = re.compile(r"\(?\b[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b")


class TextCleaner:
    """
    Clean and normalize resume text fields.

    Args:
        text_column:    Name of the column containing raw resume text.
        id_column:      Optional ID column (used for logging only).
        min_chars:      Records with cleaned text shorter than this are flagged.
        drop_flagged:   If True, flagged records are dropped. If False, retained
                        with a `_text_clean_flag` column set.
        mask_pii:       If True, mask detected email addresses and phone numbers.
    """

    def __init__(
        self,
        text_column: str,
        id_column: Optional[str] = None,
        min_chars: int = 100,
        drop_flagged: bool = False,
        mask_pii: bool = False,
    ) -> None:
        self.text_column = text_column
        self.id_column = id_column
        self.min_chars = min_chars
        self.drop_flagged = drop_flagged
        self.mask_pii = mask_pii

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clean(self, df: pd.DataFrame, show_progress: bool = False) -> pd.DataFrame:
        """
        Apply full cleaning pipeline to a copy of df.

        Returns:
            Cleaned DataFrame with column `_text_clean_flag` added.
        """
        if self.text_column not in df.columns:
            raise ValueError(
                f"Text column '{self.text_column}' not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )

        out = df.copy()
        logger.info(
            f"[CLEANER] Cleaning {len(out):,} records "
            f"(column='{self.text_column}', min_chars={self.min_chars})"
        )

        # 1. Fill NaN with empty string
        out[self.text_column] = out[self.text_column].fillna("").astype(str)

        # 2. Iterate and clean with optional tqdm progress
        if show_progress:
            try:
                from tqdm import tqdm
                cleaned_list = [self.clean_single(t) for t in tqdm(out[self.text_column], desc="Cleaning text", leave=False)]
                cleaned_series = pd.Series(cleaned_list, index=out.index)
            except ImportError:
                cleaned_series = out[self.text_column].apply(self.clean_single)
        else:
            cleaned_series = out[self.text_column].apply(self.clean_single)

        out[self.text_column] = cleaned_series

        # 3. Flag short / empty records
        out["_text_clean_flag"] = out[self.text_column].apply(self._flag)

        flagged_count = (out["_text_clean_flag"] != "ok").sum()
        empty_count = int((out["_text_clean_flag"] == "empty").sum())
        short_count = int((out["_text_clean_flag"] == "short").sum())

        logger.info(
            f"[CLEANER] Flagged {flagged_count:,} records "
            f"(empty={empty_count}, short={short_count})"
        )

        if self.drop_flagged:
            before = len(out)
            out = out[out["_text_clean_flag"] == "ok"].copy()
            logger.info(f"[CLEANER] Dropped {before - len(out):,} flagged records")

        return out  # type: ignore

    def clean_single(self, text: str) -> str:
        """Clean a single text string safely while preserving tech terms."""
        if not text or pd.isna(text) or text == "nan":
            return ""
        text = self._normalize_unicode(str(text))
        text = self._remove_artifacts(text)
        if self.mask_pii:
            text = EMAIL_PATTERN.sub("[EMAIL]", text)
            text = PHONE_PATTERN.sub("[PHONE]", text)
        return text.strip()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_unicode(text: str) -> str:
        """NFC normalization + replace common mojibake sequences."""
        text = unicodedata.normalize("NFC", text)
        replacements = {
            "\u2019": "'",   # right single quotation
            "\u2018": "'",   # left single quotation
            "\u201c": '"',   # left double quotation
            "\u201d": '"',   # right double quotation
            "\u2013": "-",   # en-dash
            "\u2014": "-",   # em-dash
            "\u00a0": " ",   # non-breaking space
            "\ufeff": "",    # BOM
            "\u2022": " ",   # bullet
            "\u2026": "...", # ellipsis
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text

    @staticmethod
    def _remove_artifacts(text: str) -> str:
        """Remove common PDF/OCR extraction artifacts from resume text."""
        # Duplicate section headers
        text = _DUPLICATE_HEADER_PATTERN.sub(r"\1", text)

        # Apply ordered artifact patterns
        for pattern, replacement in _ARTIFACT_PATTERNS:
            text = pattern.sub(replacement, text)

        return text

    def _flag(self, text: str) -> str:
        """Return a quality flag string for a single cleaned text."""
        if not text or len(text.strip()) == 0:
            return "empty"
        if len(text.strip()) < self.min_chars:
            return "short"
        return "ok"
