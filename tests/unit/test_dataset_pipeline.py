"""
TalentFlow AI — Dataset Pipeline Tests
=========================================
Tests for the data loading, cleaning, deduplication, normalization,
splitting, and validation pipeline.

Tests are skipped until the dataset is present (Stage A → Stage B gate).
After data/raw/clean_resume_data.csv is uploaded, remove the skip decorators
(or set DATASET_AVAILABLE=1 environment variable) to enable full test execution.

Run with:
    pytest tests/unit/test_dataset_pipeline.py -v
    DATASET_AVAILABLE=1 pytest tests/unit/test_dataset_pipeline.py -v
"""

import os
import sys
import pytest
from pathlib import Path

# Bootstrap backend path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

DATASET_PATH = _REPO_ROOT / "data" / "raw" / "clean_resume_data.csv"
DATASET_AVAILABLE = (
    DATASET_PATH.is_file()
    or os.environ.get("DATASET_AVAILABLE", "0").lower() in ("1", "true", "yes")
)

# Skip marker: applied to tests that require the actual dataset
require_dataset = pytest.mark.skipif(
    not DATASET_AVAILABLE,
    reason=(
        "Dataset not yet uploaded. "
        "Place data/raw/clean_resume_data.csv and re-run, "
        "or set DATASET_AVAILABLE=1."
    ),
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df():
    """Small in-memory DataFrame simulating a two-column resume dataset."""
    import pandas as pd
    return pd.DataFrame(
        {
            "ID": [1, 2, 3, 4, 5, 6],
            "Category": [
                "Data Scientist",
                "Software Engineer",
                "Data Scientist",
                "DevOps Engineer",
                "Software Engineer",
                "Software Engineer",
            ],
            "Resume_str": [
                "Python machine learning tensorflow pandas scikit-learn. " * 10,
                "Java Spring Boot REST API microservices docker kubernetes. " * 10,
                "Python machine learning tensorflow pandas scikit-learn. " * 10,  # exact dup of row 0
                "Docker kubernetes AWS CI/CD jenkins terraform ansible. " * 10,
                "Java Spring Boot REST API microservices docker kubernetes. " * 10,  # exact dup of row 1
                "Python Django Flask REST API PostgreSQL Redis SQLAlchemy. " * 10,
            ],
        }
    )


# ---------------------------------------------------------------------------
# DatasetLoader tests
# ---------------------------------------------------------------------------

class TestDatasetLoader:
    """Tests for loader.py — schema inspection and safe loading."""

    def test_loader_raises_on_missing_file(self):
        from app.data.loader import DatasetLoader
        loader = DatasetLoader(raw_path="/nonexistent/path/file.csv")
        assert not loader.exists()
        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_loader_raises_on_unsupported_extension(self, tmp_path):
        from app.data.loader import DatasetLoader
        f = tmp_path / "data.xlsx"
        f.write_text("dummy")
        loader = DatasetLoader(raw_path=f)
        with pytest.raises(ValueError, match="Unsupported file extension"):
            loader.load()

    def test_loader_loads_small_csv(self, tmp_path):
        import pandas as pd
        from app.data.loader import DatasetLoader

        test_df = pd.DataFrame({"col_a": [1, 2, 3], "col_b": ["x", "y", "z"]})
        csv_path = tmp_path / "test.csv"
        test_df.to_csv(csv_path, index=False)

        loader = DatasetLoader(raw_path=csv_path)
        df = loader.load()

        assert len(df) == 3
        assert "col_a" in df.columns
        assert "col_b" in df.columns

    def test_schema_summary_structure(self, tmp_path):
        import pandas as pd
        from app.data.loader import DatasetLoader

        test_df = pd.DataFrame({"text": ["Hello world " * 20, "Python developer " * 15], "label": ["A", "B"]})
        csv_path = tmp_path / "schema_test.csv"
        test_df.to_csv(csv_path, index=False)

        loader = DatasetLoader(raw_path=csv_path)
        loader.load()
        summary = loader.schema_summary()

        assert summary["row_count"] == 2
        assert summary["column_count"] == 2
        assert "text" in summary["columns"]
        assert "label" in summary["columns"]
        assert summary["columns"]["text"]["null_pct"] == 0.0

    def test_schema_summary_requires_load_first(self, tmp_path):
        from app.data.loader import DatasetLoader
        loader = DatasetLoader(raw_path=tmp_path / "x.csv")
        with pytest.raises(RuntimeError, match="Call load\\(\\)"):
            loader.schema_summary()

    @require_dataset
    def test_real_dataset_loads(self):
        from app.data.loader import DatasetLoader
        loader = DatasetLoader(raw_path=DATASET_PATH)
        df = loader.load()
        assert len(df) > 0
        assert len(df.columns) >= 2


# ---------------------------------------------------------------------------
# TextCleaner tests
# ---------------------------------------------------------------------------

class TestTextCleaner:
    """Tests for cleaner.py — text normalization."""

    def test_cleaner_handles_nan(self):
        import pandas as pd
        from app.data.cleaner import TextCleaner

        df = pd.DataFrame({"text": [None, "", "Hello world " * 20], "label": ["A", "B", "C"]})
        cleaner = TextCleaner(text_column="text", min_chars=50)
        out = cleaner.clean(df)

        assert out["text"].isna().sum() == 0
        assert "_text_clean_flag" in out.columns

    def test_cleaner_flags_short_text(self):
        import pandas as pd
        from app.data.cleaner import TextCleaner

        df = pd.DataFrame({"text": ["short", "x" * 200], "label": ["A", "B"]})
        cleaner = TextCleaner(text_column="text", min_chars=100)
        out = cleaner.clean(df)

        assert out.iloc[0]["_text_clean_flag"] == "short"
        assert out.iloc[1]["_text_clean_flag"] == "ok"

    def test_cleaner_preserves_technical_terms(self):
        import pandas as pd
        from app.data.cleaner import TextCleaner

        technical = "Python C++ C# Node.js React.js scikit-learn TensorFlow PyTorch PostgreSQL"
        df = pd.DataFrame({"text": [technical * 5], "label": ["A"]})
        cleaner = TextCleaner(text_column="text", min_chars=10)
        out = cleaner.clean(df)

        cleaned = out.iloc[0]["text"]
        for term in ["Python", "C++", "C#", "Node.js", "React.js", "scikit-learn"]:
            assert term in cleaned, f"Technical term '{term}' was stripped"

    def test_cleaner_raises_on_missing_column(self):
        import pandas as pd
        from app.data.cleaner import TextCleaner

        df = pd.DataFrame({"other": ["x"]})
        cleaner = TextCleaner(text_column="text")
        with pytest.raises(ValueError, match="not found"):
            cleaner.clean(df)

    def test_clean_single(self):
        from app.data.cleaner import TextCleaner
        cleaner = TextCleaner(text_column="dummy")
        # NFC normalization + mojibake replacement
        text = "Python\u2019s DataFrame and Redis\u2019 config"
        result = cleaner.clean_single(text)
        assert "\u2019" not in result
        assert "Python" in result


# ---------------------------------------------------------------------------
# Deduplicator tests
# ---------------------------------------------------------------------------

class TestDeduplicator:
    """Tests for deduplicator.py — exact and near-dup detection."""

    def test_exact_duplicates_detected(self, sample_df):
        from app.data.deduplicator import Deduplicator
        dedup = Deduplicator(text_column="Resume_str", id_column="ID", skip_near_dup=True)
        out = dedup.detect(sample_df)

        # Rows 2 and 4 (0-indexed: rows 2, 4) are exact dups of rows 0 and 1
        assert "_exact_dup" in out.columns
        exact_count = out["_exact_dup"].sum()
        assert exact_count == 2, f"Expected 2 exact dups, got {exact_count}"

    def test_dedup_report_structure(self, sample_df):
        from app.data.deduplicator import Deduplicator
        dedup = Deduplicator(text_column="Resume_str", id_column="ID", skip_near_dup=True)
        dedup.detect(sample_df)
        report = dedup.get_report()

        assert "resume_id" in report.columns
        assert "duplicate_of" in report.columns
        assert "duplicate_type" in report.columns
        assert "similarity" in report.columns
        assert "action" in report.columns

    def test_no_false_positives_on_unique_texts(self):
        import pandas as pd
        from app.data.deduplicator import Deduplicator

        df = pd.DataFrame({
            "ID": [1, 2, 3],
            "text": [
                "Python machine learning " * 20,
                "Java Spring Boot enterprise " * 20,
                "React TypeScript frontend " * 20,
            ],
        })
        dedup = Deduplicator(text_column="text", id_column="ID", skip_near_dup=True)
        out = dedup.detect(df)
        assert out["_exact_dup"].sum() == 0


# ---------------------------------------------------------------------------
# DataSplitter tests
# ---------------------------------------------------------------------------

class TestDataSplitter:
    """Tests for splitter.py — leakage-safe train/val/test split."""

    def test_split_ratios_approximate(self, sample_df):
        from app.data.splitter import DataSplitter
        splitter = DataSplitter(
            text_column="Resume_str",
            label_column="Category",
            id_column="ID",
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15,
            seed=42,
        )
        train_df, val_df, test_df = splitter.split(sample_df)

        total = len(train_df) + len(val_df) + len(test_df)
        assert total == len(sample_df), "No records should be lost"

    def test_no_leakage_by_id(self, sample_df):
        from app.data.splitter import DataSplitter
        splitter = DataSplitter(
            text_column="Resume_str",
            label_column="Category",
            id_column="ID",
            seed=42,
        )
        train_df, val_df, test_df = splitter.split(sample_df)
        leaks = splitter.verify_no_leakage(train_df, val_df, test_df)

        assert leaks["train_val_overlap"] == 0, "train/val overlap detected"
        assert leaks["train_test_overlap"] == 0, "train/test overlap detected"
        assert leaks["val_test_overlap"] == 0, "val/test overlap detected"

    def test_reproducible_with_same_seed(self, sample_df):
        from app.data.splitter import DataSplitter
        splitter_a = DataSplitter(text_column="Resume_str", label_column="Category", seed=42)
        splitter_b = DataSplitter(text_column="Resume_str", label_column="Category", seed=42)

        train_a, val_a, test_a = splitter_a.split(sample_df)
        train_b, val_b, test_b = splitter_b.split(sample_df)

        assert list(train_a.index) == list(train_b.index)
        assert list(test_a.index) == list(test_b.index)

    def test_invalid_ratio_raises(self):
        from app.data.splitter import DataSplitter
        with pytest.raises(ValueError, match="sum to 1.0"):
            DataSplitter(
                text_column="text",
                label_column="label",
                train_ratio=0.8,
                val_ratio=0.2,
                test_ratio=0.2,  # sums to 1.2
            )


# ---------------------------------------------------------------------------
# DataValidator tests
# ---------------------------------------------------------------------------

class TestDataValidator:
    """Tests for validator.py — schema and quality validation."""

    def test_validator_passes_good_data(self, sample_df):
        from app.data.validator import DataValidator
        validator = DataValidator(
            text_column="Resume_str",
            label_column="Category",
            id_column="ID",
            min_text_chars=50,
        )
        results = validator.validate(sample_df)
        assert results["passed"] is True
        assert len(results["errors"]) == 0

    def test_validator_fails_missing_column(self, sample_df):
        from app.data.validator import DataValidator
        validator = DataValidator(
            text_column="nonexistent_column",
            label_column="Category",
        )
        results = validator.validate(sample_df)
        assert results["passed"] is False
        assert any("nonexistent_column" in e for e in results["errors"])

    def test_validator_warns_on_nulls(self):
        import pandas as pd
        from app.data.validator import DataValidator

        df = pd.DataFrame({
            "text": [None, "Python developer " * 20, "React developer " * 20],
            "label": ["A", "B", "C"],
        })
        validator = DataValidator(text_column="text", label_column="label", max_null_pct=50.0)
        results = validator.validate(df)
        # Should warn (1 null = 33%) but pass since under 50% threshold
        assert results["passed"] is True
        assert any("null" in w.lower() for w in results["warnings"])


# ---------------------------------------------------------------------------
# DataNormalizer tests
# ---------------------------------------------------------------------------

class TestDataNormalizer:
    """Tests for normalizer.py — role label normalization."""

    def test_normalize_with_empty_map_keeps_original(self, sample_df):
        from app.data.normalizer import DataNormalizer
        normalizer = DataNormalizer(role_column="Category", normalization_map={})
        out = normalizer.normalize_roles(sample_df)
        assert list(out["Category"]) == list(sample_df["Category"])

    def test_normalize_applies_mapping(self):
        import pandas as pd
        from app.data.normalizer import DataNormalizer

        df = pd.DataFrame({"role": ["Data Science", "Python Developer", "Unknown"]})
        norm_map = {"Data Science": "Data Scientist"}
        normalizer = DataNormalizer(role_column="role", normalization_map=norm_map)
        out = normalizer.normalize_roles(df)

        assert out.iloc[0]["role"] == "Data Scientist"
        assert out.iloc[1]["role"] == "Python Developer"  # unchanged
        assert out.iloc[2]["role"] == "Unknown"  # unchanged (not strict)

    def test_normalize_flags_changed_rows(self):
        import pandas as pd
        from app.data.normalizer import DataNormalizer

        df = pd.DataFrame({"role": ["Data Science", "Data Scientist"]})
        norm_map = {"Data Science": "Data Scientist"}
        normalizer = DataNormalizer(role_column="role", normalization_map=norm_map)
        out = normalizer.normalize_roles(df)

        assert bool(out.iloc[0]["_role_normalized"]) is True
        assert bool(out.iloc[1]["_role_normalized"]) is False


# ---------------------------------------------------------------------------
# Integration: Stage B gate
# ---------------------------------------------------------------------------

class TestStageBGate:
    """Verify that Stage B pipeline works end-to-end once dataset is present."""

    @require_dataset
    def test_full_pipeline_smoke(self):
        """
        Smoke test for the full pipeline using the real dataset.
        Only runs when DATASET_AVAILABLE=1 or dataset file is present.
        """
        from app.data.loader import DatasetLoader
        from app.data.cleaner import TextCleaner
        from app.data.validator import DataValidator
        from app.data.deduplicator import Deduplicator
        from app.data.splitter import DataSplitter

        # Load
        loader = DatasetLoader(raw_path=DATASET_PATH)
        df = loader.load()
        assert len(df) > 0

        # Detect columns
        cols = list(df.columns)
        text_col = next((c for c in ["Resume_str", "resume_str", "text", "Feature"] if c in cols), None)
        label_col = next((c for c in ["Category", "category", "role", "label"] if c in cols), None)
        assert text_col is not None, f"Cannot find text column in {cols}"
        assert label_col is not None, f"Cannot find label column in {cols}"

        # Clean
        cleaner = TextCleaner(text_column=text_col, min_chars=100)
        df = cleaner.clean(df)

        # Validate
        validator = DataValidator(text_column=text_col, label_column=label_col, min_text_chars=100)
        results = validator.validate(df)
        assert results["passed"], f"Validation failed: {results['errors']}"

        # Dedup (exact only for speed in smoke test)
        dedup = Deduplicator(text_column=text_col, skip_near_dup=True)
        df = dedup.detect(df)

        # Split
        df_clean = df[df["_dup_action"] == "keep"].copy()
        splitter = DataSplitter(text_column=text_col, label_column=label_col, seed=42)
        train_df, val_df, test_df = splitter.split(df_clean)

        # Verify leakage
        leaks = splitter.verify_no_leakage(train_df, val_df, test_df)
        assert leaks["train_val_overlap"] == 0
        assert leaks["train_test_overlap"] == 0
        assert leaks["val_test_overlap"] == 0
