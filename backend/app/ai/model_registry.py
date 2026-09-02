"""
TalentFlow AI — Model Registry & Version Tracking
Tracks AI model versions, embedding model names, and scoring algorithm versions
for match result audit trails and reproducibility.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Current production model configuration
CURRENT_CONFIG = {
    "embedding_model": "sentence-transformers/all-mpnet-base-v2",
    "embedding_dimension": 768,
    "llm_model": "mistralai/Mistral-7B-Instruct-v0.2",
    "scoring_algorithm": "calibrated-sigmoid-v3.2",
    "scoring_version": "v3.2",
    "skill_extractor_version": "triple-layer-v1.0",
    "resume_parser_version": "multi-layer-v1.0",
    "rag_version": "hybrid-retrieval-v1.0",
}


def get_model_version() -> str:
    """Get the current composite model version string."""
    return f"{CURRENT_CONFIG['embedding_model'].split('/')[-1]}-{CURRENT_CONFIG['scoring_algorithm']}"


def get_model_metadata() -> Dict[str, Any]:
    """Get full model metadata for audit trail."""
    return {
        **CURRENT_CONFIG,
        "composite_version": get_model_version(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_scoring_config_version() -> str:
    """Get the current scoring algorithm version."""
    return CURRENT_CONFIG["scoring_version"]


def get_embedding_model_name() -> str:
    """Get the current embedding model name."""
    return CURRENT_CONFIG["embedding_model"]


def get_embedding_dimension() -> int:
    """Get the embedding vector dimension."""
    return CURRENT_CONFIG["embedding_dimension"]


class ModelRegistry:
    """Registry for tracking deployed model versions and comparing compatibility."""

    _instance: Optional['ModelRegistry'] = None

    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {
            "embedding": {
                "name": CURRENT_CONFIG["embedding_model"],
                "version": "v2",
                "dimension": CURRENT_CONFIG["embedding_dimension"],
                "provider": "huggingface",
            },
            "llm": {
                "name": CURRENT_CONFIG["llm_model"],
                "version": "v0.2",
                "provider": "huggingface",
            },
            "scorer": {
                "name": "TalentFlowScorer",
                "version": CURRENT_CONFIG["scoring_version"],
                "algorithm": CURRENT_CONFIG["scoring_algorithm"],
            },
            "skill_extractor": {
                "name": "TripleLayerExtractor",
                "version": CURRENT_CONFIG["skill_extractor_version"],
            },
        }

    @classmethod
    def get_instance(cls) -> 'ModelRegistry':
        if cls._instance is None:
            cls._instance = ModelRegistry()
        return cls._instance

    def get_model_info(self, model_type: str) -> Optional[Dict[str, Any]]:
        """Get info for a specific model type."""
        return self.models.get(model_type)

    def is_compatible(self, model_type: str, version: str) -> bool:
        """Check if a stored result was produced by a compatible model version."""
        info = self.models.get(model_type)
        if not info:
            return False
        return info.get("version") == version

    def to_dict(self) -> Dict[str, Any]:
        """Serialize full registry state."""
        return {
            "models": self.models,
            "composite_version": get_model_version(),
        }
