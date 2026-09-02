"""
TalentFlow AI — AI Engine Package (10 Modules)
"""
from .resume_parser import extract_text_from_file, extract_sections
from .text_processor import clean_text, normalize_for_matching, chunk_text
from .skill_extractor import extract_skills, categorize_skills
from .embeddings import get_embedding, cosine_similarity
from .vector_store import VectorStore
from .matching_engine import compute_match
from .ranking_model import rank_candidates, compute_tier
from .explainability import generate_match_explanation
from .rag import rag_coach
from .model_registry import ModelRegistry, get_model_version, get_model_metadata

__all__ = [
    "extract_text_from_file",
    "extract_sections",
    "clean_text",
    "normalize_for_matching",
    "chunk_text",
    "extract_skills",
    "categorize_skills",
    "get_embedding",
    "cosine_similarity",
    "VectorStore",
    "compute_match",
    "rank_candidates",
    "compute_tier",
    "generate_match_explanation",
    "rag_coach",
    "ModelRegistry",
    "get_model_version",
    "get_model_metadata",
]

