"""
TalentFlow AI — Dataset Loader
================================
Safe CSV/JSON loading with schema inspection, encoding detection,
and a human-readable schema summary.

IMPORTANT: This module is TRAINING INFRASTRUCTURE only.
It must never be imported by the production application at runtime.

Usage:
    from backend.app.data.loader import DatasetLoader

    loader = DatasetLoader(raw_path="data/raw/clean_resume_data.csv")
    df = loader.load()
    print(loader.schema_summary())
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd

logger = logging.getLogger(__name__)


class DatasetLoader:
    """
    Safe dataset loader with schema inspection.

    Attributes:
        raw_path: Absolute or relative path to the source CSV.
        encoding:  Character encoding to use (auto-detected if None).
        df:        The loaded DataFrame (None until load() is called).
    """

    SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".jsonl", ".json"}

    def __init__(
        self,
        raw_path: str | Path,
        encoding: str = "utf-8",
        max_rows: Optional[int] = None,
    ) -> None:
        self.raw_path = Path(raw_path).resolve()
        self.encoding = encoding
        self.max_rows = max_rows
        self.df: Optional[pd.DataFrame] = None
        self._load_errors: List[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def exists(self) -> bool:
        """Return True if the source file is present on disk."""
        return self.raw_path.is_file()

    def load(self) -> pd.DataFrame:
        """
        Load the dataset from disk.  Returns a DataFrame.

        Raises:
            FileNotFoundError: if the source file does not exist.
            ValueError:        if the file extension is unsupported.
        """
        if not self.exists():
            raise FileNotFoundError(
                f"Dataset not found at: {self.raw_path}\n"
                "Ensure the file has been placed at the correct location before running."
            )

        ext = self.raw_path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension '{ext}'. "
                f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        logger.info(f"[LOADER] Loading dataset: {self.raw_path}")

        try:
            if ext in (".csv", ".tsv"):
                sep = "\t" if ext == ".tsv" else ","
                self.df = pd.read_csv(
                    self.raw_path,
                    encoding=self.encoding,
                    sep=sep,
                    nrows=self.max_rows,
                    low_memory=False,
                )
            elif ext == ".jsonl":
                self.df = pd.read_json(
                    self.raw_path,
                    lines=True,
                    nrows=self.max_rows,
                )
            elif ext == ".json":
                self.df = pd.read_json(self.raw_path, nrows=self.max_rows)

        except UnicodeDecodeError:
            logger.warning(
                f"[LOADER] UTF-8 decode failed, retrying with latin-1: {self.raw_path}"
            )
            self.df = pd.read_csv(
                self.raw_path,
                encoding="latin-1",
                nrows=self.max_rows,
                low_memory=False,
            )
            self._load_errors.append("Encoding fallback: utf-8 failed, used latin-1")

        logger.info(
            f"[LOADER] Loaded {len(self.df):,} rows × {len(self.df.columns)} columns"  # type: ignore
        )
        return self.df  # type: ignore

    def schema_summary(self) -> Dict[str, Any]:
        """
        Return a dictionary describing the dataset schema.
        Must be called after load().
        """
        if self.df is None:
            raise RuntimeError("Call load() before schema_summary().")

        df = self.df
        summary: Dict[str, Any] = {
            "file": str(self.raw_path),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": {},
            "load_errors": self._load_errors,
        }

        for col in df.columns:
            col_data = df[col]
            col_info: Dict[str, Any] = {
                "dtype": str(col_data.dtype),
                "null_count": int(col_data.isna().sum()),  # type: ignore
                "null_pct": round(col_data.isna().mean() * 100, 2),
                "unique_count": int(col_data.nunique()),  # type: ignore
            }

            if col_data.dtype == object:
                lengths = col_data.dropna().astype(str).str.len()
                if len(lengths) > 0:
                    col_info["min_length"] = int(lengths.min())
                    col_info["max_length"] = int(lengths.max())
                    col_info["mean_length"] = round(float(lengths.mean()), 1)
            else:
                try:
                    col_info["min"] = float(col_data.min())  # type: ignore
                    col_info["max"] = float(col_data.max())  # type: ignore
                    col_info["mean"] = round(float(col_data.mean()), 4)  # type: ignore
                except Exception:
                    pass

            # Sample values (non-null, up to 5)
            sample = col_data.dropna().head(5).tolist()
            col_info["sample_values"] = [str(v)[:120] for v in sample]

            summary["columns"][col] = col_info

        return summary

    def print_schema(self) -> None:
        """Print a human-readable schema report to stdout."""
        s = self.schema_summary()
        print(f"\n{'='*60}")
        print(f"DATASET SCHEMA REPORT")
        print(f"File    : {s['file']}")
        print(f"Rows    : {s['row_count']:,}")
        print(f"Columns : {s['column_count']}")
        if s["load_errors"]:
            print(f"Warnings: {'; '.join(s['load_errors'])}")
        print(f"{'='*60}")
        for col, info in s["columns"].items():
            print(f"\n  [{col}]")
            print(f"    dtype       : {info['dtype']}")
            print(f"    nulls       : {info['null_count']:,} ({info['null_pct']}%)")
            print(f"    unique      : {info['unique_count']:,}")
            if "min_length" in info:
                print(
                    f"    text_length : min={info['min_length']} "
                    f"avg={info['mean_length']} max={info['max_length']}"
                )
            if "min" in info:
                print(f"    range       : {info['min']} – {info['max']} (mean {info['mean']})")
            print(f"    sample      : {info['sample_values'][:3]}")
        print(f"\n{'='*60}\n")
