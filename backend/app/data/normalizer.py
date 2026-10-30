"""
TalentFlow AI — Data Normalizer
==================================
Normalizes role labels and skills discovered in the dataset.

Design rules:
  - Do NOT blindly merge categories — only normalize where justified
  - Preserve genuinely different professions even if name overlaps
  - Normalization table is populated from actual dataset inspection (24 canonical categories)
  - Skills are normalized only where safe synonyms are confirmed

IMPORTANT: This module is TRAINING INFRASTRUCTURE only.
It must never be imported by the production application at runtime.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Role Normalization Map (Mapped to the 24 Canonical Dataset Categories)
# ---------------------------------------------------------------------------
ROLE_NORMALIZATION_MAP: Dict[str, str] = {
    # Direct mappings for the 24 categories in clean_resume_data.csv
    "ACCOUNTANT": "ACCOUNTANT",
    "ADVOCATE": "ADVOCATE",
    "AGRICULTURE": "AGRICULTURE",
    "APPAREL": "APPAREL",
    "ARTS": "ARTS",
    "AUTOMOBILE": "AUTOMOBILE",
    "AVIATION": "AVIATION",
    "BANKING": "BANKING",
    "BPO": "BPO",
    "BUSINESS-DEVELOPMENT": "BUSINESS-DEVELOPMENT",
    "CHEF": "CHEF",
    "CONSTRUCTION": "CONSTRUCTION",
    "CONSULTANT": "CONSULTANT",
    "DESIGNER": "DESIGNER",
    "DIGITAL-MEDIA": "DIGITAL-MEDIA",
    "ENGINEERING": "ENGINEERING",
    "FINANCE": "FINANCE",
    "FITNESS": "FITNESS",
    "HEALTHCARE": "HEALTHCARE",
    "HR": "HR",
    "INFORMATION-TECHNOLOGY": "INFORMATION-TECHNOLOGY",
    "PUBLIC-RELATIONS": "PUBLIC-RELATIONS",
    "SALES": "SALES",
    "TEACHER": "TEACHER",

    # Common text / whitespace / naming variants
    "ACCOUNTING": "ACCOUNTANT",
    "AUDITOR": "ACCOUNTANT",
    "BOOKKEEPER": "ACCOUNTANT",
    "LAWYER": "ADVOCATE",
    "ATTORNEY": "ADVOCATE",
    "LEGAL COUNSEL": "ADVOCATE",
    "FARMING": "AGRICULTURE",
    "AGRONOMY": "AGRICULTURE",
    "FASHION": "APPAREL",
    "TEXTILE": "APPAREL",
    "FINE ARTS": "ARTS",
    "ARTIST": "ARTS",
    "AUTOMOTIVE": "AUTOMOBILE",
    "AEROSPACE": "AVIATION",
    "PILOT": "AVIATION",
    "INVESTMENT BANKING": "BANKING",
    "CALL CENTER": "BPO",
    "CUSTOMER SUPPORT": "BPO",
    "CUSTOMER SERVICE": "BPO",
    "BUSINESS DEVELOPMENT": "BUSINESS-DEVELOPMENT",
    "BDM": "BUSINESS-DEVELOPMENT",
    "COOK": "CHEF",
    "CULINARY": "CHEF",
    "CIVIL CONSTRUCTION": "CONSTRUCTION",
    "BUILDING": "CONSTRUCTION",
    "MANAGEMENT CONSULTANT": "CONSULTANT",
    "STRATEGY CONSULTANT": "CONSULTANT",
    "GRAPHIC DESIGNER": "DESIGNER",
    "UI/UX DESIGNER": "DESIGNER",
    "DIGITAL MEDIA": "DIGITAL-MEDIA",
    "DIGITAL MARKETING": "DIGITAL-MEDIA",
    "SOCIAL MEDIA": "DIGITAL-MEDIA",
    "MECHANICAL ENGINEERING": "ENGINEERING",
    "ELECTRICAL ENGINEERING": "ENGINEERING",
    "CIVIL ENGINEERING": "ENGINEERING",
    "FINANCIAL ANALYST": "FINANCE",
    "PERSONAL TRAINER": "FITNESS",
    "GYM INSTRUCTOR": "FITNESS",
    "NURSE": "HEALTHCARE",
    "MEDICAL": "HEALTHCARE",
    "HUMAN RESOURCES": "HR",
    "RECRUITER": "HR",
    "TALENT ACQUISITION": "HR",
    "INFORMATION TECHNOLOGY": "INFORMATION-TECHNOLOGY",
    "IT": "INFORMATION-TECHNOLOGY",
    "SOFTWARE ENGINEER": "INFORMATION-TECHNOLOGY",
    "SOFTWARE DEVELOPER": "INFORMATION-TECHNOLOGY",
    "PUBLIC RELATIONS": "PUBLIC-RELATIONS",
    "PR": "PUBLIC-RELATIONS",
    "SALES REPRESENTATIVE": "SALES",
    "ACCOUNT MANAGER": "SALES",
    "EDUCATOR": "TEACHER",
    "INSTRUCTOR": "TEACHER",
    "PROFESSOR": "TEACHER",
}

# ---------------------------------------------------------------------------
# Skill Normalization Map (common safe synonyms only)
# ---------------------------------------------------------------------------
SKILL_NORMALIZATION_MAP: Dict[str, str] = {
    "scikit learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "tensorflow 2": "TensorFlow",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",
    "vuejs": "Vue",
    "vue.js": "Vue",
    "node js": "Node.js",
    "nodejs": "Node.js",
    "next js": "Next.js",
    "nextjs": "Next.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "k8s": "Kubernetes",
    "py": "Python",
}


class DataNormalizer:
    """
    Normalize role labels and (optionally) skill text in a DataFrame.

    Args:
        role_column:         Name of the column containing role/category labels.
        normalization_map:   Role label -> canonical label mapping.
        case_sensitive:      If False, matching is done case-insensitively.
        unknown_label:       Label assigned to roles not found in the map
                             when strict=True. If None, original label is kept.
        strict:              If True, roles not in map are assigned unknown_label.
                             If False (default), unrecognized roles are kept as-is.
    """

    def __init__(
        self,
        role_column: str,
        normalization_map: Optional[Dict[str, str]] = None,
        case_sensitive: bool = False,
        unknown_label: Optional[str] = None,
        strict: bool = False,
    ) -> None:
        self.role_column = role_column
        self.normalization_map = normalization_map if normalization_map is not None else ROLE_NORMALIZATION_MAP
        self.case_sensitive = case_sensitive
        self.unknown_label = unknown_label
        self.strict = strict

        # Build lookup (optionally lowercased)
        self._lookup: Dict[str, str] = {}
        for src, tgt in self.normalization_map.items():
            key = src if case_sensitive else src.strip().lower()
            self._lookup[key] = tgt

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def normalize_roles(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply role normalization.

        Returns a copy with role column normalized and a
        `_role_normalized` boolean column indicating which rows changed.
        """
        if self.role_column not in df.columns:
            raise ValueError(
                f"Role column '{self.role_column}' not found. "
                f"Available: {list(df.columns)}"
            )

        out = df.copy()
        original = out[self.role_column].astype(str)
        normalized = original.apply(self._normalize_single_role)

        changed = (original != normalized).sum()
        out[self.role_column] = normalized
        out["_role_normalized"] = original != normalized

        logger.info(
            f"[NORMALIZER] Role normalization: {changed:,} labels changed "
            f"out of {len(out):,} records"
        )

        # Report unknown labels if strict mode
        if self.strict and self.unknown_label:
            unknown_count = (out[self.role_column] == self.unknown_label).sum()
            logger.info(f"[NORMALIZER] Unknown/unmapped roles: {unknown_count:,}")

        return out

    def get_category_distribution(self, df: pd.DataFrame) -> pd.Series:
        """Return value counts for the role column."""
        if self.role_column not in df.columns:
            raise ValueError(f"Column '{self.role_column}' not found.")
        return df[self.role_column].value_counts()

    def generate_mapping_report(self, df: pd.DataFrame, output_path: Optional[str | Path] = None) -> pd.DataFrame:
        """
        Generate a category mapping DataFrame showing original -> canonical category mapping
        and record counts.
        """
        if self.role_column not in df.columns:
            raise ValueError(f"Column '{self.role_column}' not found.")

        rows = []
        for cat in df[self.role_column].unique():
            canonical = self._normalize_single_role(str(cat))
            count = int((df[self.role_column] == cat).sum())
            rows.append({
                "source_category": cat,
                "canonical_category": canonical,
                "record_count": count,
                "is_normalized": cat != canonical,
            })

        report_df = pd.DataFrame(rows).sort_values("record_count", ascending=False)
        if output_path:
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            report_df.to_csv(p, index=False)
            logger.info(f"[NORMALIZER] Category mapping report written to {p}")
        return report_df

    def summary(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Return a summary of category counts before normalization would be applied.
        """
        dist = df[self.role_column].value_counts()
        return {
            "total_categories": int(dist.shape[0]),
            "largest_category_count": int(dist.iloc[0]) if len(dist) else 0,
            "smallest_category_count": int(dist.iloc[-1]) if len(dist) else 0,
            "categories_under_10_samples": int((dist < 10).sum()),
            "categories_under_50_samples": int((dist < 50).sum()),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_single_role(self, role: str) -> str:
        """Map a single role label to its canonical form."""
        role_stripped = role.strip()
        key = role_stripped if self.case_sensitive else role_stripped.lower()

        if key in self._lookup:
            return self._lookup[key]

        if self.strict and self.unknown_label:
            return self.unknown_label

        return role_stripped  # Keep as-is if not in map and not strict


# ---------------------------------------------------------------------------
# Standalone helpers
# ---------------------------------------------------------------------------

def build_normalization_map_from_inspection(
    df: pd.DataFrame,
    role_column: str,
    threshold: int = 10,
) -> Tuple[Dict[str, str], List[str]]:
    """
    Utility to assist Stage B map construction.

    Returns:
        (suggested_merges, weak_classes)
        - suggested_merges: dict of possible normalizations (manual review required)
        - weak_classes: list of categories with fewer than `threshold` samples
    """
    dist = df[role_column].value_counts()
    weak_classes = dist[dist < threshold].index.tolist()  # type: ignore

    all_labels = dist.index.tolist()
    suggested: Dict[str, str] = {}
    for i, label_a in enumerate(all_labels):
        for label_b in all_labels[i + 1:]:
            a_lower = label_a.lower().strip()  # type: ignore
            b_lower = label_b.lower().strip()  # type: ignore
            if a_lower in b_lower or b_lower in a_lower:
                shorter = label_a if len(label_a) <= len(label_b) else label_b  # type: ignore
                longer = label_b if len(label_a) <= len(label_b) else label_a  # type: ignore
                suggested[longer] = shorter  # type: ignore

    return suggested, weak_classes  # type: ignore
