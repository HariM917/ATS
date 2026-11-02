"""
TalentFlow AI — Production 22-Class Occupational Classifier Service.

Architecture & Heritage:
- Model Version: v21-v23-final
- Taxonomy Version: 22-class-occupational-v1
- Verified 22-class occupational taxonomy (excluding legacy non-occupational industry tags: AUTOMOBILE, BPO).
- Fully decoupled from legacy resume_classifier.pkl.
- Recruiter safety review gating: review_required = confidence < 0.40 OR margin < 0.15.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import joblib
from scipy.sparse import hstack, csr_matrix

logger = logging.getLogger(__name__)

# Official 22-Class Occupational Taxonomy
CLASSES_22 = [
    "ACCOUNTANT", "ADVOCATE", "AGRICULTURE", "APPAREL", "ARTS",
    "AVIATION", "BANKING", "BUSINESS-DEVELOPMENT", "CHEF", "CONSTRUCTION",
    "CONSULTANT", "DESIGNER", "DIGITAL-MEDIA", "ENGINEERING", "FINANCE",
    "FITNESS", "HEALTHCARE", "HR", "INFORMATION-TECHNOLOGY", "PUBLIC-RELATIONS",
    "SALES", "TEACHER"
]

MODEL_VERSION = "v21-v23-final"
TAXONOMY_VERSION = "22-class-occupational-v1"

# Safety Thresholds
MIN_CONFIDENCE_THRESHOLD = 0.40
MIN_MARGIN_THRESHOLD = 0.15


class ModelNotLoadedError(Exception):
    """Raised when the occupational classification model bundle is not loaded or missing."""
    pass


class OccupationalClassifierService:
    """Production service for 22-class occupational resume classification."""

    def __init__(self, model_bundle_path: Optional[str] = None):
        self.model_bundle_path = model_bundle_path or os.environ.get(
            "OCCUPATIONAL_MODEL_PATH",
            self._default_bundle_path()
        )
        self.bundle: Optional[Dict[str, Any]] = None
        self._embedding_model = None
        self._is_loaded = False

    @staticmethod
    def _default_bundle_path() -> str:
        """Resolve path to the packaged V21 production bundle across local and container environments."""
        current_file = Path(__file__).resolve()
        candidates = [
            # 1. Local repo workspace root (backend/app/services/ -> repo root / data / ...)
            current_file.parents[3] / "data" / "processed" / "models" / "v21_production_bundle.joblib",
            # 2. Container workdir (/app/app/services/ -> /app/data / ...)
            current_file.parents[2] / "data" / "processed" / "models" / "v21_production_bundle.joblib",
            # 3. Absolute container path fallbacks
            Path("/app/data/processed/models/v21_production_bundle.joblib"),
            Path("/data/processed/models/v21_production_bundle.joblib"),
        ]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        # Default to primary workspace candidate if not yet loaded
        return str(candidates[0])

    def load_model(self, force_reload: bool = False) -> None:
        """Load the V21 production bundle from disk."""
        if self._is_loaded and not force_reload:
            return

        if not os.path.exists(self.model_bundle_path):
            raise ModelNotLoadedError(
                f"Occupational model bundle not found at '{self.model_bundle_path}'. "
                f"Verify model export or check OCCUPATIONAL_MODEL_PATH."
            )

        try:
            logger.info(f"[OCCUPATIONAL] Loading 22-class production bundle from: {self.model_bundle_path}")
            self.bundle = joblib.load(self.model_bundle_path)
            self._is_loaded = True
            logger.info("[OCCUPATIONAL] V21 production model successfully loaded into memory.")
        except Exception as e:
            self._is_loaded = False
            raise ModelNotLoadedError(f"Failed to load occupational model bundle: {e}") from e

    def _get_embedding(self, text: str) -> np.ndarray:
        """Compute or extract 768-dimensional sentence embedding."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer("all-mpnet-base-v2")
            except Exception as e:
                logger.warning(f"[OCCUPATIONAL] SentenceTransformer unavailable ({e}), using zero-embedding fallback.")
                return np.zeros((1, 768), dtype=np.float32)

        emb = self._embedding_model.encode([text], normalize_embeddings=True)
        return np.asarray(emb, dtype=np.float32)

    def predict(self, text: str, include_specific_role: bool = False) -> Dict[str, Any]:
        """
        Classify a single resume text into the 22-class occupational taxonomy.

        Returns:
            Dict conforming to the production response contract.
        """
        if not self._is_loaded:
            self.load_model()

        if self.bundle is None:
            raise ModelNotLoadedError("Model bundle is None despite load attempt.")

        # Clean input text
        clean_text = str(text or "").strip()
        if not clean_text:
            resp = self._empty_response()
            if include_specific_role:
                resp["specific_role"] = "General Specialist"
                resp["specific_role_confidence"] = 0.50
                resp["occupational_domain"] = resp["predicted_role"]
            return resp

        # 1. Transform Lexical TF-IDF features
        vec_hyb = self.bundle["vec_hybrid"]
        X_tw = vec_hyb.transform([clean_text])

        # 2. Compute MPNet Embedding
        X_mp = self._get_embedding(clean_text)

        # 3. Stack hybrid representation
        X_hyb = hstack([csr_matrix(X_mp * 0.3), X_tw])

        # 4. Predict calibrated probabilities
        clf = self.bundle["hybrid_clf"]
        raw_probs = clf.predict_proba(X_hyb)

        # Re-order to canonical 22 classes
        reorder_idx = self.bundle["reorder_hybrid"]
        p_22 = raw_probs[:, reorder_idx].squeeze()

        # Enforce strict probability normalization (simplex sum == 1.0)
        p_sum = float(np.sum(p_22))
        if p_sum > 0:
            p_22 = p_22 / p_sum
        else:
            p_22 = np.ones(len(CLASSES_22), dtype=np.float64) / len(CLASSES_22)

        # 5. Extract Top-1 and Top-2 predictions
        sorted_indices = np.argsort(-p_22)
        top1_idx = int(sorted_indices[0])
        top2_idx = int(sorted_indices[1])

        predicted_role = CLASSES_22[top1_idx]
        confidence = float(np.round(p_22[top1_idx], 4))

        runner_up_role = CLASSES_22[top2_idx]
        runner_up_confidence = float(np.round(p_22[top2_idx], 4))

        margin = float(np.round(confidence - runner_up_confidence, 4))

        # 6. Safety Rule Evaluation
        review_required, review_reasons = self._evaluate_safety_rules(
            confidence=confidence,
            margin=margin,
            predicted_role=predicted_role,
            runner_up_role=runner_up_role
        )

        response = {
            "predicted_role": predicted_role,
            "confidence": confidence,
            "runner_up_role": runner_up_role,
            "runner_up_confidence": runner_up_confidence,
            "margin": margin,
            "review_required": review_required,
            "review_reasons": review_reasons,
            "model_version": MODEL_VERSION,
            "taxonomy_version": TAXONOMY_VERSION,
        }

        # 7. Secondary Specific Role Specialization Layer (optional enrichment)
        if include_specific_role:
            from .role_service import RoleService
            specific_role, specific_role_confidence = RoleService.predict_specific_role(
                resume_text=clean_text,
                occupational_class=predicted_role
            )
            response["specific_role"] = specific_role
            response["specific_role_confidence"] = specific_role_confidence
            response["occupational_domain"] = predicted_role.replace("-", " ").title()

        return response

    def predict_specialized(self, text: str) -> Dict[str, Any]:
        """Convenience method returning 22-class domain + secondary role specialization."""
        return self.predict(text, include_specific_role=True)

    def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Classify a batch of resume texts."""
        return [self.predict(t) for t in texts]

    @staticmethod
    def _evaluate_safety_rules(
        confidence: float,
        margin: float,
        predicted_role: str,
        runner_up_role: str
    ) -> Tuple[bool, List[str]]:
        """
        Evaluate recruiter review triggers based on V23 error analysis.
        Gating Rule: review_required = confidence < 0.40 OR margin < 0.15.
        """
        reasons = []
        if confidence < MIN_CONFIDENCE_THRESHOLD:
            reasons.append(
                f"Low prediction confidence ({confidence:.2f} < {MIN_CONFIDENCE_THRESHOLD:.2f})"
            )
        if margin < MIN_MARGIN_THRESHOLD:
            reasons.append(
                f"Thin top-2 probability margin ({margin:.2f} < {MIN_MARGIN_THRESHOLD:.2f}) "
                f"between '{predicted_role}' and runner-up '{runner_up_role}'"
            )

        review_required = len(reasons) > 0
        return review_required, reasons

    @staticmethod
    def _empty_response() -> Dict[str, Any]:
        """Return standardized empty / fallback response."""
        return {
            "predicted_role": "UNKNOWN",
            "confidence": 0.0,
            "runner_up_role": "UNKNOWN",
            "runner_up_confidence": 0.0,
            "margin": 0.0,
            "review_required": True,
            "review_reasons": ["Empty resume text provided"],
            "model_version": MODEL_VERSION,
            "taxonomy_version": TAXONOMY_VERSION,
            "specific_role": "Software Engineer",
            "specific_role_confidence": 0.0,
            "occupational_domain": "Information Technology"
        }


# Singleton Pattern for Production Reuse
_instance: Optional[OccupationalClassifierService] = None


def get_occupational_classifier() -> OccupationalClassifierService:
    """Get or initialize the occupational classifier singleton."""
    global _instance
    if _instance is None:
        _instance = OccupationalClassifierService()
        try:
            _instance.load_model()
        except Exception as e:
            logger.warning(f"[OCCUPATIONAL] Lazy initialization warning: {e}")
    return _instance
