"""
TalentFlow AI — Report Generator
===================================
Generates:
  - data/reports/dataset_inspection_report.md
  - data/reports/dataset_statistics.json
  - data/reports/quality_report.csv
  - data/reports/class_distribution.csv
  - data/reports/duplicates.csv
  - data/reports/manual_review.csv
  - data/reports/category_mapping.csv
  - data/dataset_manifest.json

IMPORTANT: This module is TRAINING INFRASTRUCTURE only.
It must never be imported by the production application at runtime.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Current preprocessing pipeline version
PREPROCESSING_VERSION = "1.0.0"


class ReportGenerator:
    """
    Write dataset quality reports, manual review queues, and manifests to disk.

    Args:
        output_dir: Directory where reports will be written.
                    Created if it does not exist.
    """

    def __init__(self, output_dir: str | Path = "data/reports") -> None:
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Dataset Inspection Report (.md)
    # ------------------------------------------------------------------

    def write_inspection_report(
        self,
        schema_summary: Dict[str, Any],
        validation_results: Dict[str, Any],
        df: pd.DataFrame,
        label_column: str,
        text_column: str,
        id_column: Optional[str] = None,
    ) -> Path:
        """
        Write a comprehensive Markdown inspection report for human review.
        """
        stats = validation_results.get("stats", {})
        dist = df[label_column].value_counts()
        total_rows = len(df)
        total_cols = len(df.columns)
        null_count = df.isnull().sum().sum()
        exact_dup_rows = df.duplicated().sum()
        dup_ids = df[id_column].duplicated().sum() if id_column and id_column in df.columns else 0

        md_lines = [
            "# Dataset Inspection Report",
            "",
            f"**File**: `{schema_summary.get('file', 'clean_resume_data.csv')}`  ",
            f"**Inspection Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Pipeline Version**: {PREPROCESSING_VERSION}  ",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            f"| Metric | Value |",
            f"|---|---|",
            f"| **Total Rows** | `{total_rows:,}` |",
            f"| **Total Columns** | `{total_cols}` |",
            f"| **Columns Present** | `{', '.join(df.columns.tolist())}` |",
            f"| **Missing / Null Values** | `{null_count:,}` |",
            f"| **Duplicate Rows (Full)** | `{exact_dup_rows:,}` |",
            f"| **Duplicate IDs** | `{dup_ids:,}` |",
            f"| **Unique Categories** | `{len(dist)}` |",
            "",
            "---",
            "",
            "## 2. Column Schema Analysis",
            "",
            "| Column Name | Data Type | Null Count | Null % | Unique Values | Sample Value |",
            "|---|---|---|---|---|---|",
        ]

        for col, col_info in schema_summary.get("columns", {}).items():
            sample_val = col_info.get("sample_values", ["N/A"])[0].replace("|", "\\|").replace("\n", " ")[:60]
            md_lines.append(
                f"| `{col}` | `{col_info.get('dtype')}` | `{col_info.get('null_count'):,}` | "
                f"`{col_info.get('null_pct')}%` | `{col_info.get('unique_count'):,}` | `{sample_val}...` |"
            )

        md_lines.extend([
            "",
            "---",
            "",
            "## 3. Text Length & Word Count Statistics",
            "",
            f"| Statistic | Character Count | Word Count |",
            f"|---|---|---|",
            f"| **Minimum** | `{stats.get('min_length', 0):,}` chars | `{stats.get('min_words', 0):,}` words |",
            f"| **Mean (Average)** | `{stats.get('mean_length', 0):,}` chars | `{stats.get('mean_words', 0):,}` words |",
            f"| **Median** | `{stats.get('median_length', 0):,}` chars | `~{int(stats.get('mean_words', 0)):,}` words |",
            f"| **Maximum** | `{stats.get('max_length', 0):,}` chars | `{stats.get('max_words', 0):,}` words |",
            f"| **Empty Records** | `{stats.get('empty_text', 0):,}` | `{stats.get('empty_text', 0):,}` |",
            f"| **Short (<100 chars)** | `{stats.get('short_char_records', 0):,}` | — |",
            "",
            "---",
            "",
            "## 4. Category Distribution",
            "",
            "| Rank | Category Name | Record Count | Percentage of Total |",
            "|---|---|---|---|",
        ])

        for rank, (cat_name, count) in enumerate(dist.items(), start=1):
            pct = count / total_rows * 100
            md_lines.append(f"| {rank} | `{cat_name}` | `{count:,}` | `{pct:.2f}%` |")

        md_lines.extend([
            "",
            "---",
            "",
            "## 5. Detected Data Issues & Flagged Items",
            "",
        ])

        if validation_results.get("errors"):
            md_lines.append("### Critical Errors")
            for err in validation_results["errors"]:
                md_lines.append(f"- ❌ **ERROR**: {err}")
            md_lines.append("")

        if validation_results.get("warnings"):
            md_lines.append("### Quality Warnings")
            for warn in validation_results["warnings"]:
                md_lines.append(f"- ⚠️ **WARNING**: {warn}")
            md_lines.append("")
        else:
            md_lines.append("✅ No quality warnings detected.")

        report_path = self.output_dir / "dataset_inspection_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        logger.info(f"[REPORT] Inspection report written to: {report_path}")
        return report_path

    # ------------------------------------------------------------------
    # 2. Dataset Statistics (.json)
    # ------------------------------------------------------------------

    def write_dataset_statistics(
        self,
        schema_summary: Dict[str, Any],
        validation_results: Dict[str, Any],
        df: pd.DataFrame,
        label_column: str,
        text_column: str,
    ) -> Path:
        """
        Write detailed dataset statistics as a structured JSON file.
        """
        texts = df[text_column].dropna().astype(str)
        char_lengths = texts.str.len()
        word_counts = texts.apply(lambda x: len(x.split()))

        dist = df[label_column].value_counts().to_dict()

        stats = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_version": PREPROCESSING_VERSION,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "null_values_per_column": df.isnull().sum().to_dict(),
            "unique_categories_count": int(df[label_column].nunique()),  # type: ignore
            "category_distribution": dist,
            "text_character_statistics": {
                "min": int(char_lengths.min()) if len(char_lengths) > 0 else 0,  # type: ignore
                "max": int(char_lengths.max()) if len(char_lengths) > 0 else 0,  # type: ignore
                "mean": round(float(char_lengths.mean()), 2) if len(char_lengths) > 0 else 0.0,  # type: ignore
                "median": float(char_lengths.median()) if len(char_lengths) > 0 else 0.0,  # type: ignore
                "std": round(float(char_lengths.std()), 2) if len(char_lengths) > 0 else 0.0,  # type: ignore
            },
            "text_word_statistics": {
                "min": int(word_counts.min()) if len(word_counts) > 0 else 0,  # type: ignore
                "max": int(word_counts.max()) if len(word_counts) > 0 else 0,  # type: ignore
                "mean": round(float(word_counts.mean()), 2) if len(word_counts) > 0 else 0.0,  # type: ignore
                "median": float(word_counts.median()) if len(word_counts) > 0 else 0.0,  # type: ignore
                "std": round(float(word_counts.std()), 2) if len(word_counts) > 0 else 0.0,  # type: ignore
            },
            "validation_results": validation_results,
        }

        path = self.output_dir / "dataset_statistics.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)

        logger.info(f"[REPORT] Dataset statistics JSON written to: {path}")
        return path

    # ------------------------------------------------------------------
    # 3. Quality Report (.csv)
    # ------------------------------------------------------------------

    def write_quality_report(
        self,
        validation_results: Dict[str, Any],
        schema_summary: Optional[Dict[str, Any]] = None,
    ) -> Path:
        rows = []
        stats = validation_results.get("stats", {})

        rows.append({
            "check": "total_records",
            "value": stats.get("total_records", "N/A"),
            "status": "info",
            "detail": "Total records in dataset",
        })
        rows.append({
            "check": "empty_text_records",
            "value": stats.get("empty_text", 0),
            "status": "warn" if stats.get("empty_text", 0) > 0 else "ok",
            "detail": "Records with null or empty text",
        })
        rows.append({
            "check": "short_char_records",
            "value": stats.get("short_char_records", 0),
            "status": "warn" if stats.get("short_char_records", 0) > 0 else "ok",
            "detail": "Records below character length threshold",
        })
        rows.append({
            "check": "suspicious_records",
            "value": stats.get("suspicious_records", 0),
            "status": "warn" if stats.get("suspicious_records", 0) > 0 else "ok",
            "detail": "Records with HTML or symbol garbage",
        })
        rows.append({
            "check": "min_text_length",
            "value": stats.get("min_length", "N/A"),
            "status": "info",
            "detail": "Shortest text record (chars)",
        })
        rows.append({
            "check": "max_text_length",
            "value": stats.get("max_length", "N/A"),
            "status": "info",
            "detail": "Longest text record (chars)",
        })
        rows.append({
            "check": "mean_text_length",
            "value": stats.get("mean_length", "N/A"),
            "status": "info",
            "detail": "Mean text length (chars)",
        })

        for error in validation_results.get("errors", []):
            rows.append({
                "check": "validation_error",
                "value": None,
                "status": "error",
                "detail": error,
            })
        for warning in validation_results.get("warnings", []):
            rows.append({
                "check": "validation_warning",
                "value": None,
                "status": "warn",
                "detail": warning,
            })

        if schema_summary:
            for col, col_info in schema_summary.get("columns", {}).items():
                rows.append({
                    "check": f"column_{col}_null_pct",
                    "value": col_info.get("null_pct", "N/A"),
                    "status": "warn" if col_info.get("null_pct", 0) > 5 else "ok",
                    "detail": f"Null percentage for column '{col}'",
                })

        report_df = pd.DataFrame(rows)
        report_path = self.output_dir / "quality_report.csv"
        report_df.to_csv(report_path, index=False)
        logger.info(f"[REPORT] Quality report written: {report_path}")
        return report_path

    # ------------------------------------------------------------------
    # 4. Class Distribution (.csv)
    # ------------------------------------------------------------------

    def write_class_distribution(
        self,
        df: pd.DataFrame,
        label_column: str,
    ) -> Path:
        if label_column not in df.columns:
            raise ValueError(f"Column '{label_column}' not found in DataFrame.")

        dist = df[label_column].value_counts().reset_index()
        dist.columns = ["category", "count"]
        dist["percentage"] = (dist["count"] / dist["count"].sum() * 100).round(2)
        dist["rank"] = range(1, len(dist) + 1)

        path = self.output_dir / "class_distribution.csv"
        dist.to_csv(path, index=False)
        logger.info(f"[REPORT] Class distribution written: {path} ({len(dist)} categories)")
        return path

    # ------------------------------------------------------------------
    # 5. Duplicate Report (.csv)
    # ------------------------------------------------------------------

    def write_duplicate_report(self, dup_df: pd.DataFrame) -> Path:
        path = self.output_dir / "duplicates.csv"
        dup_df.to_csv(path, index=False)
        logger.info(f"[REPORT] Duplicate report written: {path} ({len(dup_df):,} flagged records)")
        return path

    # ------------------------------------------------------------------
    # 6. Manual Review Queue (.csv)
    # ------------------------------------------------------------------

    def write_manual_review_queue(
        self,
        review_records: List[Dict[str, Any]],
    ) -> Path:
        """
        Write data/reports/manual_review.csv with flagged questionable records.

        Columns:
            resume_id, category, issue_type, severity, resume_text, recommended_action, human_decision
        """
        columns = [
            "resume_id",
            "category",
            "issue_type",
            "severity",
            "resume_text",
            "recommended_action",
            "human_decision",
        ]
        if review_records:
            df_review = pd.DataFrame(review_records)
            for c in columns:
                if c not in df_review.columns:
                    df_review[c] = ""
            df_review = df_review[columns]
        else:
            df_review = pd.DataFrame(columns=columns)

        path = self.output_dir / "manual_review.csv"
        df_review.to_csv(path, index=False)
        logger.info(f"[REPORT] Manual review queue written: {path} ({len(df_review):,} records for review)")
        return path

    # ------------------------------------------------------------------
    # 7. Dataset Manifest (.json)
    # ------------------------------------------------------------------

    def write_manifest(self, manifest_data: Dict[str, Any]) -> Path:
        manifest = {
            "dataset_version": manifest_data.get("dataset_version", "2026.09"),
            "source": manifest_data.get("source", "clean_resume_data.csv"),
            "source_file": manifest_data.get("source_file", "clean_resume_data.csv"),
            "source_sha256": manifest_data.get("source_sha256", ""),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "preprocessing_version": PREPROCESSING_VERSION,
            "split_seed": manifest_data.get("split_seed", 42),
            "row_count": manifest_data.get("row_count", 0),
            "clean_row_count": manifest_data.get("clean_row_count", 0),
            "flagged_count": manifest_data.get("flagged_count", 0),
            "removed_count": manifest_data.get("removed_count", 0),
            "train_count": manifest_data.get("train_count", 0),
            "validation_count": manifest_data.get("validation_count", 0),
            "test_count": manifest_data.get("test_count", 0),
            "category_count": manifest_data.get("category_count", 0),
            "duplicate_count": manifest_data.get("duplicate_count", 0),
            "near_duplicate_count": manifest_data.get("near_duplicate_count", 0),
            "text_column": manifest_data.get("text_column", "Feature"),
            "label_column": manifest_data.get("label_column", "Category"),
            "id_column": manifest_data.get("id_column", "ID"),
            "columns": manifest_data.get("columns", []),
            "notes": manifest_data.get("notes", "Cleaned by TalentFlow AI Hybrid Preprocessing Pipeline"),
        }

        path = self.output_dir.parent / "dataset_manifest.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"[REPORT] Dataset manifest written: {path}")
        return path
