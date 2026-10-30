"""
TalentFlow AI — Data Pipeline Package
======================================
Provides modular data loading, cleaning, deduplication, normalization,
splitting, validation, and reporting for the ATS training dataset.

Usage:
    from backend.app.data.loader import DatasetLoader
    from backend.app.data.cleaner import TextCleaner
    # ... etc.

This package is TRAINING INFRASTRUCTURE only.
It must never become a runtime dependency for ATS candidate matching.

Pipeline flow (orchestrated by scripts/build_dataset.py):
    raw CSV
        ↓ loader.py     — safe load, schema inspection
        ↓ validator.py  — schema + quality checks
        ↓ cleaner.py    — text normalization
        ↓ deduplicator.py — exact + near-dup detection
        ↓ normalizer.py — role label + skill normalization
        ↓ taxonomy.py   — controlled category taxonomy
        ↓ splitter.py   — train/val/test split (leakage-safe)
        ↓ report.py     — quality_report, class_distribution, manifest
"""

__version__ = "1.0.0"

# Public API — imported on-demand in build_dataset.py to keep startup light
__all__ = [
    "DatasetLoader",
    "TextCleaner",
    "DataNormalizer",
    "Deduplicator",
    "DataTaxonomy",
    "DataSplitter",
    "DataValidator",
    "ReportGenerator",
]
